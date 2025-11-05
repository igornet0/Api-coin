import asyncio
import pandas as pd
from datetime import datetime
from kucoin.client import User, Trade, Market
import aiohttp
import asyncio
from src.parser_driver.api import ParserApi
from src.core import settings_parser
from src.core.models.dataset import DatasetTimeseries

import logging

time_in_int = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "1h": 60,
    "2h": 120,
    "4h": 240,
    "8h": 480,
    "12h": 720,
    "1d": 1440,
    "1w": 10080,
}

def formating_datetime(x):
    try:
        x = int(x)
        # если значение слишком большое — миллисекунды
        if x > 1e12:
            x = x / 1000
        return datetime.fromtimestamp(x)
    except Exception as e:
        return pd.NaT

class KuCoinAPI(ParserApi):
        
    api_key = settings_parser.kucoin.api_key
    api_secret = settings_parser.kucoin.api_secret
    api_passphrase = settings_parser.kucoin.api_passphrase

    args_entry = (api_key, api_secret, api_passphrase)
    
    user = User(*args_entry)
    trade = Trade(*args_entry)
    market = Market(*args_entry)

    logger = logging.getLogger("parser_logger.KuCoinAPI")

    max_concurrent = 100  # Максимальное количество одновременных запросов

    def get_account_summary_info(self):
        return self.user.get_account_summary_info()

    @classmethod
    def get_stat_24hr(cls, symbol: str, currency: str = "USDT") -> dict:
        """
        {
            "time": 1602832092060, // time
            "symbol": "BTC-USDT", // symbol
            "buy": "11328.9", // bestAsk
            "sell": "11329", // bestBid
            "changeRate": "-0.0055", // 24h change rate
            "changePrice": "-63.6", // 24h change price
            "high": "11610", // 24h highest price
            "low": "11200", // 24h lowest price
            "vol": "2282.70993217", // 24h volume the aggregated trading volume in BTC
            "volValue": "25984946.157790431", // 24h total, the trading volume in quote currency of last 24 hours
            "last": "11328.9", // last price
            "averagePrice": "11360.66065903", // 24h average transaction price yesterday
            "takerFeeRate": "0.001", // Basic Taker Fee
            "makerFeeRate": "0.001", // Basic Maker Fee
            "takerCoefficient": "1", // Taker Fee Coefficient
            "makerCoefficient": "1" // Maker Fee Coefficient
        }
        """
        return cls.market.get_24hr_stats(f"{symbol}-{currency}")
    
    @classmethod
    def get_orders_market(cls, symbol: str, currency: str = "USDT"):
        return cls.market.get_order_book(f"{symbol}-{currency}")

    @classmethod
    async def async_parsed_coins(cls, coins_last_datetime: dict[str, datetime],
                                 currency: str = "USDT",
                                time: str | int = "5m") -> dict[str, DatasetTimeseries | None]:

        semaphore = asyncio.Semaphore(cls.max_concurrent)
        
        async def fetch(symbol, last_dt, time):
            async with semaphore:
                try:
                    if "FUTURE" in symbol:

                        if isinstance(time, str):
                            time = time_in_int[time]
                        else:
                            time = int(time)

                        result = await cls.get_kline_futures(symbol, time, last_dt)
                    else:
                        result = await cls.get_kline(symbol, currency, time, last_dt)
                except Exception as e:
                    cls.logger.error(f"Error get kline {symbol}-{currency} - {e}")
                    result = None
                return result
        
            # tasks = [fetch(session, sym, dt) for sym, dt in coins_last_datetime.items()]
        # async with aiohttp.ClientSession() as session:    
        results = await asyncio.gather(*[fetch(sym, dt, time) for sym, dt in coins_last_datetime.items()], return_exceptions=True)
            
        return results

    @classmethod
    async def get_kline(cls, symbol: str, 
                             currency: str = "USDT",
                             time: str = "5m",
                             last_datetime: datetime = None) -> DatasetTimeseries | None:

        # cls.logger.info(f"Get coin: {symbol} time: {time=} last_datetime: {last_datetime=}")
        
        if time[-1] == "m":
            time = time.replace("m", "min")
        elif time[-1] == "H":
            time = time.replace("H", "hour")
        elif time[-1] == "D":
            time = time.replace("D", "day")
        elif time[-1] == "W":
            time = time.replace("W", "week")

        try:
            data = await cls.market.async_get_kline(f"{symbol}-{currency}", time)
        except Exception as e:
            cls.logger.error(f"Error get kline {symbol}-{currency} - {e}")
            return None

        colums = ["datetime", "open", "close", "max", "min", "_", "volume"]

        df = pd.DataFrame(data, columns=colums).drop("_", axis=1)

        if len(df) == 0:
            cls.logger.error(f"Error get kline {symbol}-{currency} - {len(df)=}")
            return None

        df["datetime"] = df["datetime"].apply(formating_datetime)
        
        df["datetime"] = pd.to_datetime(df['datetime'])

        if last_datetime is not None:
            df = df[df["datetime"] >= last_datetime]

        if "day" in time or "week" in time:
            df["datetime"] = df["datetime"].dt.strftime('%Y-%m-%d')
        else:
            df["datetime"] = df["datetime"].dt.strftime('%Y-%m-%d %H:%M:%S')

        df["volume"] = df["volume"].apply(float)

        df = DatasetTimeseries(df)

        return symbol, df

    @classmethod
    async def get_kline_futures(cls, symbol: str, 
                             time: int = 1,
                             last_datetime: datetime = None) -> DatasetTimeseries | None:
        try:
            data = await cls.market.async_get_kline_future(symbol.replace("FUTURE_", ""), time)
        except Exception as e:
            cls.logger.error(f"Error get kline futures {symbol} - {e}")
            return None

        # cls.logger.info(f"Get kline futures {symbol} - {data=}")

        colums = ["datetime", "open", "max", "min", "close", "_", "volume"]

        df = pd.DataFrame(data, columns=colums).drop("_", axis=1)

        if len(df) == 0:
            cls.logger.error(f"Error get kline {symbol} - {len(df)=}")
            return None

        df["datetime"] = df["datetime"].apply(formating_datetime)
        
        df["datetime"] = pd.to_datetime(df['datetime'])

        if last_datetime is not None:
            df = df[df["datetime"] >= last_datetime]

        df["datetime"] = df["datetime"].dt.strftime('%Y-%m-%d %H:%M:%S')

        df["volume"] = df["volume"].apply(float)

        df = DatasetTimeseries(df)

        return symbol, df

    
    # @classmethod
    # def get_kline(cls, symbol: str, 
    #               currency: str = "USDT",
    #               time: str = "5m",
    #               last_datetime: datetime = None) -> DatasetTimeseries | None: 
    #     """
    #     "1545904980", //Start time of the candle cycle "0.058", 
    #     //opening price "0.049", 
    #     //closing price "0.058", 
    #     //highest price "0.049", 
    #     //lowest price "0.018", 
    #     //Transaction amount "0.000945" 
    #     //Transaction volume 143676
    #     """

    #     cls.logger.info(f"Get coin: {symbol} time: {time=} last_datetime: {last_datetime=}")
        
    #     if time[-1] == "m":
    #         time = time.replace("m", "min")
    #     elif time[-1] == "H":
    #         time = time.replace("H", "hour")
    #     elif time[-1] == "D":
    #         time = time.replace("D", "day")
    #     elif time[-1] == "W":
    #         time = time.replace("W", "week")

    #     try:
    #         data = cls.market.get_kline(f"{symbol}-{currency}", time)
    #     except Exception as e:
    #         cls.logger.error(f"Error get kline {symbol}-{currency} - {e}")
    #         return None

    #     colums = ["datetime", "open", "close", "max", "min", "_", "volume"]

    #     df = pd.DataFrame(data, columns=colums).drop("_", axis=1)

    #     if len(df) == 0:
    #         cls.logger.error(f"Error get kline {symbol}-{currency} - {len(df)=}")
    #         return None

    #     df["datetime"] = df["datetime"].apply(lambda x: datetime.fromtimestamp(int(x)))
        
    #     df["datetime"] = pd.to_datetime(df['datetime'])

    #     if last_datetime is not None:
    #         df = df[df["datetime"] >= last_datetime]

    #     if "day" in time or "week" in time:
    #         df["datetime"] = df["datetime"].dt.strftime('%Y-%m-%d')
    #     else:
    #         df["datetime"] = df["datetime"].dt.strftime('%Y-%m-%d %H:%M:%S')

    #     df["volume"] = df["volume"].apply(float)

    #     return DatasetTimeseries(df)