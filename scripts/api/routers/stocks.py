"""
股票数据查询接口
"""
from fastapi import APIRouter, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import date
from sqlalchemy import text

from scripts.database import get_engine

router = APIRouter()


class StockDataItem(BaseModel):
    date: date
    symbol: str
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    volume: Optional[float]
    
    class Config:
        from_attributes = True


class StockSymbol(BaseModel):
    symbol: str


@router.get("/symbols", response_model=List[StockSymbol])
async def list_symbols():
    """
    获取所有股票代码列表
    """
    engine = get_engine()
    query = text("""
        SELECT DISTINCT symbol
        FROM market_stocks_daily
        ORDER BY symbol
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query)
        rows = result.fetchall()
    
    return [StockSymbol(symbol=row.symbol) for row in rows]


@router.get("/data", response_model=List[StockDataItem])
async def get_stock_data(
    symbol: str = Query(..., description="股票代码，如 AAPL"),
    start_date: Optional[date] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    limit: int = Query(1000, ge=1, le=10000, description="返回条数限制")
):
    """
    查询指定股票的历史日线数据
    
    - symbol: 股票代码
    - start_date: 可选，默认不限制
    - end_date: 可选，默认不限制
    """
    engine = get_engine()
    
    # 构建动态 SQL
    conditions = ["symbol = :symbol"]
    params = {"symbol": symbol.upper(), "limit": limit}
    
    if start_date:
        conditions.append("date >= :start_date")
        params["start_date"] = start_date
    if end_date:
        conditions.append("date <= :end_date")
        params["end_date"] = end_date
    
    where_clause = " AND ".join(conditions)
    
    query = text(f"""
        SELECT date, symbol, open, high, low, close, volume
        FROM market_stocks_daily
        WHERE {where_clause}
        ORDER BY date DESC
        LIMIT :limit
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query, params)
        rows = result.fetchall()
    
    return [
        StockDataItem(
            date=row.date,
            symbol=row.symbol,
            open=float(row.open) if row.open else None,
            high=float(row.high) if row.high else None,
            low=float(row.low) if row.low else None,
            close=float(row.close) if row.close else None,
            volume=float(row.volume) if row.volume else None
        )
        for row in rows
    ]


@router.get("/data/latest", response_model=Optional[StockDataItem])
async def get_latest_data(symbol: str = Query(..., description="股票代码")):
    """
    获取指定股票的最新数据
    """
    engine = get_engine()
    query = text("""
        SELECT date, symbol, open, high, low, close, volume
        FROM market_stocks_daily
        WHERE symbol = :symbol
        ORDER BY date DESC
        LIMIT 1
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query, {"symbol": symbol.upper()})
        row = result.fetchone()
    
    if not row:
        return None
    
    return StockDataItem(
        date=row.date,
        symbol=row.symbol,
        open=float(row.open) if row.open else None,
        high=float(row.high) if row.high else None,
        low=float(row.low) if row.low else None,
        close=float(row.close) if row.close else None,
        volume=float(row.volume) if row.volume else None
    )
