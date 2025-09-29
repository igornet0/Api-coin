from kucoin.model_data.earn.earn import EarnData
from kucoin.model_data.lending.lending import LendingData
from kucoin.model_data.margin.margin import MarginData
from kucoin.model_data.market.market import MarketData
from kucoin.model_data.trade.trade import TradeData
from kucoin.model_data.user.user import UserData
from kucoin.ws_token.token import GetToken


class User(UserData):
    pass


class Trade(TradeData):
    pass


class Market(MarketData):
    pass


class Lending(LendingData):
    pass

class Earn(EarnData):
    pass


class Margin(MarginData):
    pass


class WsToken(GetToken):
    pass
