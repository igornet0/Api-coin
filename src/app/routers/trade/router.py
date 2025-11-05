"""
KuCoin Trade API роутер с интеграцией лимитирования
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Optional, Dict, Any
from pydantic import BaseModel
import logging
import time

from src.app.configuration.auth import verify_authorization
from src.app.services import get_ex_service
from src.core.database.orm.orm_query_order import OrderQuery
from src.core.database.orm.orm_query_coin import CoinQuery

router = APIRouter(prefix="/kucoin/trade", tags=["kucoin_trade"])
logger = logging.getLogger(__name__)


class OrderCreate(BaseModel):
    symbol: str
    side: str  # 'buy' or 'sell'
    order_type: str  # 'limit' or 'market'
    size: str
    price: Optional[str] = None
    client_oid: Optional[str] = None
    remark: Optional[str] = None


@router.post("/orders")
async def create_order(
    order_data: OrderCreate,
    api_key_id: int = Query(..., description="ID API ключа"),
    user: dict = Depends(verify_authorization)):
    """Создать ордер на KuCoin"""
    try:
        ex_service = await get_ex_service(api_key_id, user.id)
        
        order_result = await ex_service.create_order(
            symbol=order_data.symbol,
            side=order_data.side,
            order_type=order_data.order_type,
            size=order_data.size,
            price=order_data.price,
            clientOid=order_data.client_oid,
            remark=order_data.remark
        )
        
        return {
            "order": order_result,
            "api_key_id": api_key_id,
            "message": "Order created successfully"
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders")
async def get_orders(
    api_key_id: int = Query(..., description="ID API ключа"),
    symbol: Optional[str] = Query(None, description="Фильтр по торговой паре"),
    status: Optional[str] = Query(None, description="Фильтр по статусу (active, done)"),
    user: dict = Depends(verify_authorization)):
    """Получить список ордеров пользователя"""
    try:
        ex_service = await get_ex_service(api_key_id, user.id)
        orders = await ex_service.get_orders(symbol, status)
        
        return {
            "orders": orders,
            "api_key_id": api_key_id,
            "filters": {
                "symbol": symbol,
                "status": status
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/order/create")
async def create_order_in_db(
    order_data: OrderCreate,
    api_key_id: int = Query(..., description="ID API ключа"),
    user: dict = Depends(verify_authorization)):
    """Создать ордер на KuCoin и сохранить в базе данных"""
    try:
        # Получаем монету по символу
        coin = await CoinQuery.get_coin_by_symbol(order_data.symbol)
        if not coin:
            raise HTTPException(status_code=404, detail=f"Coin with symbol {order_data.symbol} not found")
        
        # Преобразуем size и price в float
        try:
            size = float(order_data.size)
            price = float(order_data.price) if order_data.price else 0.0
        except ValueError:
            raise HTTPException(status_code=400, detail="Size and price must be valid numbers")
        
        # Проверяем, что для limit ордеров указана цена
        if order_data.order_type == 'limit' and (not order_data.price or price <= 0):
            raise HTTPException(status_code=400, detail="Price is required for limit orders")
        
        # Сначала создаем ордер на KuCoin через API
        ex_service = await get_ex_service(api_key_id, user.id)
        
        order_result = await ex_service.create_order(
            symbol=order_data.symbol,
            side=order_data.side,
            order_type=order_data.order_type,
            size=order_data.size,
            price=order_data.price,
            clientOid=order_data.client_oid,
            remark=order_data.remark
        )
        
        # Извлекаем exchange_order_id из ответа KuCoin API
        # Формат ответа: {'orderId': '5d9ee461f24b80689797fd04'} или может быть 'data': {'orderId': '...'}
        exchange_order_id = None
        if isinstance(order_result, dict):
            # Проверяем различные возможные форматы ответа
            exchange_order_id = order_result.get('orderId') or order_result.get('order_id')
            if not exchange_order_id and 'data' in order_result:
                data = order_result['data']
                exchange_order_id = data.get('orderId') or data.get('order_id')
        
        if not exchange_order_id:
            # Если не удалось получить ID, пробуем использовать client_oid или генерируем временный
            exchange_order_id = order_data.client_oid or f"pending_{user.id}_{coin.id}_{int(time.time())}"
            logger.warning(f"Could not extract exchange_order_id from KuCoin response, using generated: {exchange_order_id}")
        
        # Преобразуем в строку, если это не строка
        exchange_order_id = str(exchange_order_id)
        
        # Теперь сохраняем ордер в базе данных
        order = await OrderQuery.create_order(
            user_id=user.id, 
            kucoin_api_key_id=api_key_id,
            exchange_order_id=exchange_order_id,
            coin_id=coin.id, 
            order_type=order_data.order_type, 
            side=order_data.side, 
            size=size, 
            price=price)
        
        return {
            "order": {
                "id": order.id,
                "exchange_order_id": order.exchange_order_id,
                "symbol": order_data.symbol,
                "order_type": order.order_type,
                "side": order.side,
                "size": order.size,
                "price": order.price,
                "status": order.status,
                "created": order.created.isoformat() if order.created else None
            },
            "kucoin_response": order_result,
            "message": "Order created successfully on KuCoin and saved to database"
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Error creating order: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating order: {str(e)}")


@router.delete("/order/{order_id}")
async def cancel_order(
    order_id: str,
    api_key_id: int = Query(..., description="ID API ключа"),
    user: dict = Depends(verify_authorization)):
    """Отменить ордер"""
    try:
        ex_service = await get_ex_service(api_key_id, user.id)
        result = await ex_service.cancel_order(order_id)
        
        return {
            "result": result,
            "order_id": order_id,
            "api_key_id": api_key_id,
            "message": "Order cancelled successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling order {order_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/account")
async def get_account_info(
    api_key_id: int = Query(..., description="ID API ключа"),
    currency: Optional[str] = Query(None, description="Фильтр по валюте"),
    user: dict = Depends(verify_authorization)):
    """Получить информацию об аккаунте"""
    try:
        ex_service = await get_ex_service(api_key_id, user.id)
        
        if currency:
            account_info = await ex_service.get_account_balance(currency)
        else:
            account_info = await ex_service.get_account_info()
        
        return {
            "account": account_info,
            "api_key_id": api_key_id,
            "currency_filter": currency
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting account info: {e}")
        raise HTTPException(status_code=500, detail=str(e))