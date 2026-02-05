import logging
import pandas as pd
import os
import time
import random
import yfinance as yf
from scripts.database import get_engine, ensure_hypertable

logger = logging.getLogger("quant.task.stocks")
CONFIG_FILE = "/app/config/stock_tickers.csv"

BATCH_SIZE = 20
MIN_SLEEP = 10
MAX_SLEEP = 20
RETRIES = 3
RETRY_DELAY = 5

def check_yfinance_status():
    try:
        logger.info("🔍 [自检] 正在测试 Yahoo Finance 连接...")
        df = yf.download("SPY", period="1d", progress=False, auto_adjust=True)
        
        if not df.empty:
            logger.info("✅ [自检] 连接成功，数据正常。")
            return True
        else:
            errors = getattr(yf.shared, '_ERRORS', {})
            logger.error(f"❌ [自检] 下载失败。错误详情: {errors}")
            return False
            
    except Exception as e:
        logger.error(f"❌ [自检] 代码执行异常: {e}")
        return False

def process_batch(chunk_tickers, engine, table_name):
    if not chunk_tickers: return

    tickers_str = " ".join(chunk_tickers)
    
    for attempt in range(RETRIES):
        try:
            data = yf.download(
                tickers_str, 
                period="1d", 
                group_by='ticker', 
                auto_adjust=True,
                progress=False, 
                threads=False
            )

            if data.empty:
                errors = getattr(yf.shared, '_ERRORS', {})
                logger.warning(f"⚠️ 本批次无数据: {chunk_tickers[0]}... 详情: {errors}")
                
                err_str = str(errors)
                if "429" in err_str or "Too Many Requests" in err_str:
                    raise Exception("Rate Limited (429)")
                
                return 

            db_rows = []
            
            if isinstance(data.columns, pd.MultiIndex):
                for symbol in chunk_tickers:
                    try:
                        df_symbol = data[symbol].dropna(how='all')
                        if df_symbol.empty: continue
                        
                        df_symbol = df_symbol.reset_index()
                        df_symbol.rename(columns={'Date': 'date'}, inplace=True)
                        df_symbol['symbol'] = symbol
                        df_symbol.columns = [c.lower().replace(' ', '_') for c in df_symbol.columns]
                        db_rows.append(df_symbol)
                    except KeyError:
                        continue
            else:
                symbol = chunk_tickers[0]
                df_symbol = data.dropna(how='all').reset_index()
                df_symbol.rename(columns={'Date': 'date'}, inplace=True)
                df_symbol['symbol'] = symbol
                df_symbol.columns = [c.lower().replace(' ', '_') for c in df_symbol.columns]
                db_rows.append(df_symbol)

            if db_rows:
                final_df = pd.concat(db_rows, ignore_index=True)
                if 'date' in final_df.columns and 'symbol' in final_df.columns:
                    final_df.to_sql(table_name, engine, if_exists='append', index=False)
                    logger.info(f"✅ 入库成功: {len(db_rows)} 只股票")
                else:
                    logger.error("❌ 数据格式异常: 缺少 date 或 symbol")
            
            break 

        except Exception as e:
            if attempt < RETRIES - 1:
                wait = RETRY_DELAY * (attempt + 1)
                logger.warning(f"⚠️ 下载异常，{wait}秒后重试: {e}")
                time.sleep(wait)
            else:
                logger.error(f"❌ 批次最终失败: {e}")

def fetch_stock_data():
    if not os.path.exists(CONFIG_FILE):
        logger.warning(f"⚠️ 配置文件未找到: {CONFIG_FILE}")
        return
    
    try:
        raw = pd.read_csv(CONFIG_FILE, header=None)[0].astype(str).tolist()
        tickers = sorted(list(set([x.strip().upper() for x in raw if x.strip()])))
    except Exception:
        logger.warning("⚠️ 股票列表读取失败")
        return

    logger.info(f"🐢 启动稳健采集任务 (总数: {len(tickers)} | 批次: {BATCH_SIZE})")

    engine = get_engine()
    table_name = 'market_stocks_daily'
    ensure_hypertable(table_name, 'date')

    for i in range(0, len(tickers), BATCH_SIZE):
        chunk = tickers[i : i + BATCH_SIZE]
        
        logger.info(f"🔄 [{i+1}/{len(tickers)}] 处理: {chunk[0]} ...")
        
        process_batch(chunk, engine, table_name)
        
        if i + BATCH_SIZE < len(tickers):
            sleep_time = random.uniform(MIN_SLEEP, MAX_SLEEP)
            logger.info(f"💤 休息 {sleep_time:.1f} 秒...")
            time.sleep(sleep_time)

    logger.info("🏁 股票采集任务全部完成")
