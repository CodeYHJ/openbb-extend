import logging
import pandas as pd
import os
import requests
from datetime import datetime
from openbb import obb
from sqlalchemy import text
from scripts.database import get_engine, ensure_hypertable

logger = logging.getLogger("quant.task.macro")

# 起始年份常量（获取从此年份到最新的数据）
START_YEAR = 2020

# 硬编码宏观指标数据
# 格式: (indicator_name, series_id, frequency, update_time)
MACRO_INDICATORS = [
    ("美联储总资产", "WALCL", "周 (每周三数据)", "每周四公布"),
    ("财政部一般账户 (TGA)", "WTREGEN", "周 (每周三数据)", "每周四公布"),
    ("隔夜逆回购 (ON RRP)", "RRPONTSYD", "日", "每日公布"),
    ("银行准备金总额", "TOTRESNS", "两周", "隔周周四公布"),
]

TABLE_NAME = 'macro_economic_data'


def init_macro_table(engine):
    """初始化宏观数据表结构"""
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        date DATE NOT NULL,
        series_id VARCHAR(20) NOT NULL,
        indicator_name VARCHAR(100),
        value NUMERIC,
        frequency VARCHAR(50),
        provider VARCHAR(20) DEFAULT 'fred',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (date, series_id)
    );
    """
    
    # 创建索引（如果主键未自动创建）
    create_index_sql = f"""
    CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_series_id 
    ON {TABLE_NAME} (series_id);
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.execute(text(create_index_sql))
            conn.commit()
        logger.info(f"✅ 表 {TABLE_NAME} 初始化完成")
    except Exception as e:
        logger.error(f"❌ 表初始化失败: {e}")
        raise


def delete_existing_data(engine, series_id, start_date, end_date):
    """删除指定指标在日期范围内的旧数据，避免重复"""
    delete_sql = f"""
    DELETE FROM {TABLE_NAME} 
    WHERE series_id = :series_id 
    AND date >= :start_date 
    AND date <= :end_date
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(delete_sql),
                {
                    "series_id": series_id,
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            conn.commit()
            deleted_count = result.rowcount
            if deleted_count > 0:
                logger.info(f"🗑️ 删除旧数据: {series_id} ({deleted_count} 条)")
            return deleted_count
    except Exception as e:
        logger.error(f"❌ 删除旧数据失败: {e}")
        raise


def test_fred_connectivity(api_key):
    """
    🔍 连通性测试函数
    直接访问 FRED API 一个极小的请求，验证 Key 和网络是否正常
    """
    test_url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": "GDP",
        "api_key": api_key,
        "file_type": "json",
        "limit": 1
    }
    
    try:
        response = requests.get(test_url, params=params, timeout=5)
        
        if response.status_code == 200:
            logger.info("✅ [自检] FRED API 连接成功！Key 有效。")
            return True
        elif response.status_code == 400:
            logger.error(f"❌ [自检] API Key 无效或参数错误: {response.text}")
            return False
        elif response.status_code == 403:
            logger.error(f"❌ [自检] 权限被拒绝 (可能是 IP 被封): {response.text}")
            return False
        else:
            logger.error(f"❌ [自检] 未知错误 (Code {response.status_code}): {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ [自检] 网络连接失败 (DNS/防火墙?): {str(e)}")
        return False


def fetch_macro_data():
    logger.info("🔄 开始宏观指标采集 (带连接自检)...")

    # 1. 获取并检查环境变量
    fred_key = os.getenv('FRED_API_KEY')
    if not fred_key:
        logger.error("❌ 致命错误: 未找到 FRED_API_KEY 环境变量")
        return

    # 2. 执行连通性测试
    if not test_fred_connectivity(fred_key):
        logger.error("⛔ 由于自检失败，宏观任务已终止。")
        return

    # 3. 注入 OpenBB
    obb.user.credentials.fred_api_key = fred_key
    
    # 4. 获取数据库引擎并初始化表
    engine = get_engine()
    init_macro_table(engine)
    
    # 5. 设置日期范围
    START_DATE = f"{START_YEAR}-01-01"
    END_DATE = datetime.now().strftime("%Y-%m-%d")
    logger.info(f"📅 数据日期范围: {START_DATE} ~ {END_DATE}")
    
    # 6. 转换为 Hypertable（如果还不是）
    ensure_hypertable(TABLE_NAME, 'date')

    # 7. 采集数据
    total_inserted = 0
    
    for indicator_name, series_id, frequency, _ in MACRO_INDICATORS:
        logger.info(f"📊 正在获取 {indicator_name} (ID: {series_id})...")
        try:
            # 使用 fred_series + start_date + end_date
            res = obb.economy.fred_series(
                symbol=series_id, 
                provider="fred",
                start_date=START_DATE,
                end_date=END_DATE
            )
            df = res.to_dataframe()

            if df.empty:
                logger.warning(f"⚠️ {indicator_name} 返回空数据")
                continue

            # 清洗
            df.index.name = 'date'
            df.reset_index(inplace=True)
            
            # 动态列重命名
            value_cols = [c for c in df.columns if c != 'date']
            if value_cols:
                df.rename(columns={value_cols[0]: 'value'}, inplace=True)
            else:
                logger.error(f"❌ {indicator_name} 未找到数值列")
                continue
            
            # 添加元数据
            df['series_id'] = series_id              # 真实 Series ID (WALCL)
            df['indicator_name'] = indicator_name     # 中文名称
            df['frequency'] = frequency               # 频率
            df['provider'] = 'fred'
            df['created_at'] = datetime.now()
            
            # 数据类型转换
            df['date'] = pd.to_datetime(df['date']).dt.date
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            df.dropna(subset=['value'], inplace=True)
            
            if df.empty:
                logger.warning(f"⚠️ {indicator_name} 清洗后无有效数据")
                continue
            
            # 删除旧数据（避免重复）
            delete_existing_data(engine, series_id, START_DATE, END_DATE)
            
            # 入库
            save_df = df[['date', 'series_id', 'indicator_name', 'value', 'frequency', 'provider', 'created_at']]
            save_df.to_sql(TABLE_NAME, engine, if_exists='append', index=False)
            
            inserted_count = len(save_df)
            total_inserted += inserted_count
            latest_date = df['date'].max()
            logger.info(f"✅ {indicator_name} 入库成功 (Records: {inserted_count}, Latest: {latest_date})")

        except Exception as e:
            logger.error(f"❌ {indicator_name} 采集失败: {e}")

    logger.info(f"🏁 宏观任务执行完毕，共入库 {total_inserted} 条记录")
