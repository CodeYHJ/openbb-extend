import logging
import pandas as pd
import os
import datetime
from openbb import obb
from scripts.database import get_engine, ensure_hypertable

logger = logging.getLogger("quant.task.macro")

def fetch_macro_data():
    logger.info("🔄 开始宏观指标采集 (FRED Series Mode + History Fix)...")

    # 1. 注入 Key (调试模式)
    fred_key = os.getenv('FRED_API_KEY')
    if fred_key:
        obb.user.credentials.fred_api_key = fred_key
        # 隐去中间部分打印，确认Key已读取
        visible_key = f"{fred_key[:4]}...{fred_key[-4:]}" if len(fred_key) > 8 else "***"
        logger.info(f"🔑 FRED Key Loaded: {visible_key}")
    else:
        logger.error("❌ 致命错误: 未找到 FRED_API_KEY")
        return

    # 2. 定义任务清单
    tasks = [
        ("CPI", "CPIAUCSL"), 
        ("GDP", "GDP"), 
        ("UNRATE", "UNRATE"), 
        ("FEDFUNDS", "FEDFUNDS"),
        ("M2", "M2SL") 
    ]

    engine = get_engine()
    table_name = 'macro_economic_data'

    # 3. 设定起始时间 (抓取所有历史数据)
    # 如果不设，OpenBB 可能默认只抓最近一年，导致季度数据(GDP)为空
    START_DATE = "1950-01-01"

    for name, series_id in tasks:
        logger.info(f"📊 正在获取 {name} (ID: {series_id})...")
        try:
            # --- 核心修正点 ---
            # 增加 start_date 参数，强制拉取历史数据
            res = obb.economy.fred_series(
                symbol=series_id, 
                provider="fred",
                start_date=START_DATE 
            )
            df = res.to_dataframe()

            if df.empty:
                logger.warning(f"⚠️ {name} 数据为空 (请检查 Key 是否开通了权限)")
                continue

            # 4. 数据清洗
            df.index.name = 'date'
            df.reset_index(inplace=True)
            
            # 重命名 value 列
            cols = [c for c in df.columns if c != 'date']
            if cols:
                df.rename(columns={cols[0]: 'value'}, inplace=True)
            
            df['series_id'] = name
            
            # 5. 入库
            if 'value' in df.columns:
                # 确保时间格式正确
                df['date'] = pd.to_datetime(df['date'])
                
                # 去除空值
                df.dropna(subset=['value'], inplace=True)

                # 存库
                save_df = df[['date', 'series_id', 'value']]
                save_df.to_sql(table_name, engine, if_exists='append', index=False)
                
                ensure_hypertable(table_name, 'date')
                
                # 打印最新的一条数据日期，确认不是空跑
                latest_date = df['date'].max().date()
                logger.info(f"✅ {name} 入库成功 (Records: {len(df)}, Latest: {latest_date})")
            else:
                logger.error(f"❌ {name} 格式异常: {df.columns}")

        except Exception as e:
            # 打印更详细的错误
            logger.error(f"❌ {name} 采集失败: {e}", exc_info=True)

    logger.info("🏁 宏观任务执行完毕")