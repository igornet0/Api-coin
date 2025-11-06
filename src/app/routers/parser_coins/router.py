from typing import List, Optional
import csv
import io
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.configuration import Server
from src.app.configuration.schemas import CoinResponse, TimeseriesResponse, DataTimeseriesResponse, CoinCreateRequest, CoinsUploadResponse
from src.core.database.orm import CoinQuery

router = APIRouter(prefix="/coins", tags=["coins"])

@router.get("/", response_model=List[CoinResponse])
async def get_coins(
    parsed: Optional[bool] = Query(None, description="Фильтр по статусу парсинга")):
    """
    Получить список всех монет
    """
    coins = await CoinQuery.get_coins(parsed)
    if not coins:
        raise HTTPException(status_code=404, detail="No coins found")
    
    return coins


@router.get("/{coin_name}", response_model=CoinResponse)
async def get_coin_by_name(
    coin_name: str):
    """
    Получить информацию о монете по имени
    """
    coin = await CoinQuery.get_coin_by_symbol(coin_name)
    
    if not coin:
        raise HTTPException(status_code=404, detail=f"Coin {coin_name} not found")
    
    return coin


@router.get("/{coin_name}/timeseries", response_model=List[TimeseriesResponse])
async def get_coin_timeseries(
    coin_name: str,
    timestamp: Optional[str] = Query(None, description="Фильтр по timestamp (например, 5m, 1h)")):
    """
    Получить временные ряды для монеты
    """
    coin = await CoinQuery.get_coin_by_symbol(symbol=coin_name)
    
    if not coin:
        raise HTTPException(status_code=404, detail=f"Coin {coin_name} not found")
    
    timeseries = await CoinQuery.get_timeseries_by_coin(coin=coin, timestamp=timestamp)
    
    return timeseries


@router.get("/timeseries/{timeseries_id}/data", response_model=List[DataTimeseriesResponse])
async def get_timeseries_data(
    timeseries_id: int):
    """
    Получить данные временного ряда
    """

    data = await CoinQuery.get_data_timeseries(timeseries_id)
    
    if not data:
        raise HTTPException(status_code=404, detail=f"Timeseries {timeseries_id} not found")
    
    return data


@router.post("/", response_model=CoinResponse)
async def create_coin(
    coin_data: CoinCreateRequest):
    """
    Добавить новую монету
    """
    try:
        coin = await CoinQuery.add_coin(name=coin_data.name, price_now=coin_data.price_now)
        
        # Обновляем статус парсинга если нужно
        # if coin.parsed != coin_data.parsed:
        #     from src.core.database.orm import orm_change_parsing_status_coin
        #     await orm_change_parsing_status_coin(session, coin_data.name, coin_data.parsed)
        #     coin.parsed = coin_data.parsed
        
        return coin
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка добавления монеты: {str(e)}")


@router.post("/upload", response_model=CoinsUploadResponse)
async def upload_coins_csv(
    file: UploadFile = File(..., description="CSV файл со списком монет")):
    """
    Загрузить список монет из CSV файла
    Формат CSV: колонка 'name' с названиями монет
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Файл должен быть в формате CSV")
    
    try:
        # Читаем файл
        contents = await file.read()
        contents_str = contents.decode('utf-8')
        
        # Парсим CSV
        csv_reader = csv.DictReader(io.StringIO(contents_str))
        
        added = 0
        skipped = 0
        errors = []
        coin_names = []
        
        for row in csv_reader:
            # Ищем колонку 'name' или первую непустую колонку
            coin_name = None
            
            # Приоритет колонке 'name'
            if 'name' in row and row['name']:
                coin_name = str(row['name']).strip()
            # Если нет 'name', берем первое непустое значение, пропуская первую колонку (индекс)
            elif len(row) > 0:
                values = list(row.values())
                # Пропускаем первую колонку (обычно это индекс) и ищем первое значение
                for val in values[1:] if len(values) > 1 else values:
                    if val and str(val).strip():
                        coin_name = str(val).strip()
                        break
            
            if not coin_name or coin_name == '':
                continue
            
            # Пропускаем заголовки, индексы (только цифры) и пустые строки
            if coin_name.lower() in ['name', 'coins', 'coin', ''] or coin_name.isdigit():
                continue
            
            try:
                # Проверяем существует ли монета
                existing_coin = await CoinQuery.get_coin_by_symbol(symbol=coin_name)
                if existing_coin:
                    skipped += 1
                    continue
                
                # Добавляем монету
                await CoinQuery.add_coin(name=coin_name, price_now=0)
                added += 1
                coin_names.append(coin_name)
                
            except Exception as e:
                errors.append(f"Ошибка при добавлении {coin_name}: {str(e)}")
        
        return CoinsUploadResponse(
            total=added + skipped + len(errors),
            added=added,
            skipped=skipped,
            errors=errors
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка обработки файла: {str(e)}")


@router.delete("/{coin_name}", response_model=dict)
async def delete_coin(
    coin_name: str,
    session: AsyncSession = Depends(Server.get_db)):
    """
    Удалить монету
    """
    coin = await CoinQuery.get_coin_by_symbol(symbol=coin_name)
    
    if not coin:
        raise HTTPException(status_code=404, detail=f"Coin {coin_name} not found")
    
    try:
        await CoinQuery.delete_coin(coin_name=coin_name)
        
        return {"message": f"Coin {coin_name} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка удаления монеты: {str(e)}")


@router.get("/{coin_name}/export-csv")
async def export_coin_data_timeseries_csv(
    coin_name: str,
    session: AsyncSession = Depends(Server.get_db)):
    """
    Выгрузить все данные DataTimeseries для монеты в формате CSV
    """
    coin = await CoinQuery.get_coin_by_symbol(symbol=coin_name)
    
    if not coin:
        raise HTTPException(status_code=404, detail=f"Coin {coin_name} not found")
    
    try:
        # Получаем все DataTimeseries для монеты
        data_timeseries = await CoinQuery.get_all_data_timeseries_by_coin(coin=coin)
        
        if not data_timeseries:
            raise HTTPException(status_code=404, detail=f"No data found for coin {coin_name}")
        
        # Создаем CSV в памяти
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Заголовки
        writer.writerow(['id', 'timeseries_id', 'datetime', 'open', 'max', 'min', 'close', 'volume'])
        
        # Данные
        for data in data_timeseries:
            writer.writerow([
                data.id,
                data.timeseries_id,
                data.datetime.isoformat() if data.datetime else '',
                data.open,
                data.max,
                data.min,
                data.close,
                data.volume
            ])
        
        # Получаем CSV строку
        csv_string = output.getvalue()
        output.close()
        
        # Возвращаем CSV файл
        return Response(
            content=csv_string.encode('utf-8-sig'),  # utf-8-sig для правильного отображения в Excel
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={coin_name}_data_timeseries.csv"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при выгрузке CSV: {str(e)}")

