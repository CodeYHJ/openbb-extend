"""
宏观数据查询接口
"""
from fastapi import APIRouter, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import date
from sqlalchemy import text

from scripts.database import get_engine

router = APIRouter()


class MacroDataItem(BaseModel):
    date: date
    series_id: str
    indicator_name: Optional[str]
    value: float
    frequency: Optional[str]
    provider: str
    
    class Config:
        from_attributes = True


class MacroIndicator(BaseModel):
    series_id: str
    indicator_name: str
    frequency: str


@router.get("/indicators", response_model=List[MacroIndicator])
async def list_indicators():
    """
    获取所有宏观指标列表
    """
    engine = get_engine()
    query = text("""
        SELECT DISTINCT series_id, indicator_name, frequency
        FROM macro_economic_data
        ORDER BY series_id
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query)
        rows = result.fetchall()
    
    return [
        MacroIndicator(
            series_id=row.series_id,
            indicator_name=row.indicator_name or row.series_id,
            frequency=row.frequency or "未知"
        )
        for row in rows
    ]


@router.get("/data", response_model=List[MacroDataItem])
async def get_macro_data(
    series_id: str = Query(..., description="指标代码，如 WALCL"),
    start_date: Optional[date] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    limit: int = Query(1000, ge=1, le=10000, description="返回条数限制")
):
    """
    查询指定宏观指标的历史数据
    
    - series_id: 指标代码，可通过 /indicators 接口查询
    - start_date: 可选，默认不限制
    - end_date: 可选，默认不限制
    """
    engine = get_engine()
    
    # 构建动态 SQL
    conditions = ["series_id = :series_id"]
    params = {"series_id": series_id, "limit": limit}
    
    if start_date:
        conditions.append("date >= :start_date")
        params["start_date"] = start_date
    if end_date:
        conditions.append("date <= :end_date")
        params["end_date"] = end_date
    
    where_clause = " AND ".join(conditions)
    
    query = text(f"""
        SELECT date, series_id, indicator_name, value, frequency, provider
        FROM macro_economic_data
        WHERE {where_clause}
        ORDER BY date DESC
        LIMIT :limit
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query, params)
        rows = result.fetchall()
    
    return [
        MacroDataItem(
            date=row.date,
            series_id=row.series_id,
            indicator_name=row.indicator_name,
            value=float(row.value) if row.value else 0.0,
            frequency=row.frequency,
            provider=row.provider
        )
        for row in rows
    ]


@router.get("/data/latest", response_model=Optional[MacroDataItem])
async def get_latest_data(series_id: str = Query(..., description="指标代码")):
    """
    获取指定指标的最新数据
    """
    engine = get_engine()
    query = text("""
        SELECT date, series_id, indicator_name, value, frequency, provider
        FROM macro_economic_data
        WHERE series_id = :series_id
        ORDER BY date DESC
        LIMIT 1
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query, {"series_id": series_id})
        row = result.fetchone()
    
    if not row:
        return None
    
    return MacroDataItem(
        date=row.date,
        series_id=row.series_id,
        indicator_name=row.indicator_name,
        value=float(row.value) if row.value else 0.0,
        frequency=row.frequency,
        provider=row.provider
    )
