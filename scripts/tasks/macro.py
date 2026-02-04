import logging
import pandas as pd
import os
import requests # 引入 requests 做底层诊断
from openbb import obb
from scripts.database import get_engine, ensure_hypertable

logger = logging.getLogger("quant.task.macro")

def test_fred_connectivity(api_key):
    """
    🔍 连通性测试函数
    直接访问 FRED API 一个极小的请求，验证 Key 和网络是否正常
    """
    test_url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": "GDP", # 用最基础的 GDP 做测试
        "api_key": api_key,
        "file_type": "json",
        "limit": 1 # 只取 1 条数据，极速
    }
    
    try:
        # 设置 5 秒超时，防止卡死
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

    # 2. 执行连通性测试 (新增步骤)
    # 如果这一步不通过，直接终止，不浪费时间去调 OpenBB
    if not test_fred_connectivity(fred_key):
        logger.error("⛔ 由于自检失败，宏观任务已终止。")
        return

    # 3. 注入 OpenBB
    obb.user.credentials.fred_api_key = fred_key
    
    # 4. 任务列表
    tasks = [
        ("CPI", "CPIAUCSL"), 
        ("GDP", "GDP"), 
        ("UNRATE", "UNRATE"), 
        ("FEDFUNDS", "FEDFUNDS"),
        ("M2", "M2SL") 
    ]

    engine = get_engine()
    table_name = 'macro_economic_data'
    # 强制抓取历史数据
    START_DATE = "1950-01-01"

    for name, series_id in tasks:
        logger.info(f"📊 正在获取 {name} (ID: {series_id})...")
        try:
            # 使用 fred_series + start_date
            res = obb.economy.fred_series(
                symbol=series_id, 
                provider="fred",
                start_date=START_DATE 
            )
            df = res.to_dataframe()

            if df.empty:
                logger.warning(f"⚠️ {name} 返回空数据")
                continue

            # 清洗
            df.index.name = 'date'
            df.reset_index(inplace=True)
            
            # 动态列重命名
            cols = [c for c in df.columns if c != 'date']
            if cols: df.rename(columns={cols[0]: 'value'}, inplace=True)
            
            df['series_id'] = name
            
            # 入库
            if 'value' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df.dropna(subset=['value'], inplace=True)
                
                save_df = df[['date', 'series_id', 'value']]
                save_df.to_sql(table_name, engine, if_exists='append', index=False)
                
                ensure_hypertable(table_name, 'date')
                
                latest_date = df['date'].max().date()
                logger.info(f"✅ {name} 入库成功 (Records: {len(df)}, Latest: {latest_date})")
            else:
                logger.error(f"❌ {name} 数据格式异常: {df.columns}")

        except Exception as e:
            logger.error(f"❌ {name} 采集失败: {e}")

    logger.info("🏁 宏观任务执行完毕")