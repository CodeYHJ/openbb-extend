import logging
import pandas as pd
import os
import time
import random
from openbb import obb
from scripts.database import get_engine, ensure_hypertable

logger = logging.getLogger("quant.task.stocks")
CONFIG_FILE = "/app/config/stock_tickers.csv"

def fetch_stock_data():
    if not os.path.exists(CONFIG_FILE):
        return
    
    try:
        tickers = pd.read_csv(CONFIG_FILE, header=None)[0].astype(str).tolist()
    except Exception:
        return

    logger.info(f"🚀 开始采集 {len(tickers)} 只股票 (慢速防封模式)...")
    
    engine = get_engine()
    table_name = 'market_stocks_daily'

    for i, symbol in enumerate(tickers):
        symbol = symbol.strip().upper()
        if not symbol: continue

        # 进度日志
        logger.info(f"[{i+1}/{len(tickers)}] 获取 {symbol} ...")
        
        try:
            # 1. 获取数据
            df = obb.equity.price.historical(
                symbol=symbol, 
                provider='yfinance', 
                interval='1d'
            ).to_dataframe()

            if df.empty:
                logger.warning(f"⚠️ {symbol} 为空 (可能是代码错误)")
                continue

            # 2. 清洗
            df.index.name = 'date'
            df.reset_index(inplace=True)
            if 'symbol' not in df.columns:
                df['symbol'] = symbol

            # 3. 入库
            df.to_sql(table_name, engine, if_exists='append', index=False)
            ensure_hypertable(table_name, 'date')
            
            logger.info(f"✅ {symbol} 成功")
            
            # 成功后：正常休息 3-8 秒
            time.sleep(random.uniform(3, 8))

        except Exception as e:
            err_str = str(e)
            if "Rate limited" in err_str or "Too Many Requests" in err_str:
                wait_time = random.randint(30, 60)
                logger.error(f"❌ {symbol} 触发严重限流！强制休眠 {wait_time} 秒...")
                time.sleep(wait_time) 
            else:
                logger.error(f"❌ {symbol} 失败: {e}")
                time.sleep(2) # 普通错误稍微停一下

    logger.info("🏁 股票任务结束")