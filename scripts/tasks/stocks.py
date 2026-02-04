import logging
import pandas as pd
import os
import time
import random
import yfinance as yf # 直接引入 yfinance 做底层测试
from openbb import obb
from scripts.database import get_engine, ensure_hypertable

logger = logging.getLogger("quant.task.stocks")
CONFIG_FILE = "/app/config/stock_tickers.csv"

def check_yfinance_status():
    """
    🔍 连通性测试 (金丝雀测试)
    尝试下载 SPY (标普500 ETF) 的 1 天数据，检测 IP 是否被 Yahoo 拉黑
    """
    canary = "SPY"
    logger.info(f"🔍 [自检] 正在测试 Yahoo Finance 连接 (Target: {canary})...")
    
    try:
        # 使用 yfinance 原生库测试，不经 OpenBB 包装，报错更直观
        # period="1d" 极简数据量
        df = yf.download(canary, period="1d", progress=False, auto_adjust=True)
        
        if not df.empty:
            logger.info("✅ [自检] Yahoo Finance 连接正常！IP 未被封锁。")
            return True
        else:
            logger.error("❌ [自检] 返回数据为空。可能是 IP 被临时限制，或网络不通。")
            return False
            
    except Exception as e:
        err_msg = str(e)
        if "Rate limited" in err_msg or "Too Many Requests" in err_msg:
            logger.critical("⛔ [自检] 检测到 Rate Limit！IP 已被 Yahoo 封锁。任务终止。")
        else:
            logger.error(f"❌ [自检] 连接异常: {err_msg}")
        return False

def fetch_stock_data():
    # 1. 检查配置文件
    if not os.path.exists(CONFIG_FILE):
        logger.warning(f"⚠️ 配置文件未找到: {CONFIG_FILE}")
        return
    
    try:
        tickers = pd.read_csv(CONFIG_FILE, header=None)[0].astype(str).tolist()
    except Exception:
        logger.warning("⚠️ 股票列表为空")
        return

    logger.info(f"🚀 开始股票采集任务 (目标: {len(tickers)} 只)...")

    # 2. 【新增】执行自检
    # 如果自检挂了，后面几千只股票就别试了，直接停机，防止封锁加重
    if not check_yfinance_status():
        logger.error("⛔ 自检失败，股票任务已取消。建议检查网络或更换 IP。")
        return

    # 3. 开始正式采集
    engine = get_engine()
    table_name = 'market_stocks_daily'

    for i, symbol in enumerate(tickers):
        symbol = symbol.strip().upper()
        if not symbol: continue

        # 进度条风格日志
        logger.info(f"[{i+1}/{len(tickers)}] 获取 {symbol} ...")
        
        try:
            # 调用 OpenBB 获取数据
            df = obb.equity.price.historical(
                symbol=symbol, 
                provider='yfinance', 
                interval='1d'
            ).to_dataframe()

            if df.empty:
                logger.warning(f"⚠️ {symbol} 数据为空")
                continue

            # 清洗
            df.index.name = 'date'
            df.reset_index(inplace=True)
            if 'symbol' not in df.columns:
                df['symbol'] = symbol

            # 入库
            df.to_sql(table_name, engine, if_exists='append', index=False)
            
            # 为了性能，这里可以每隔 10 只做一次 hypertable check，或者只在最后做
            # 但为了代码简单，暂时保持每次都做（开销很小，因为有 if_not_exists 判断）
            ensure_hypertable(table_name, 'date')
            
            logger.info(f"✅ {symbol} 成功")
            
            # 防封休眠 (随机 2-5 秒)
            time.sleep(random.uniform(2, 5))

        except Exception as e:
            err_str = str(e)
            if "Rate limited" in err_str or "Too Many Requests" in err_str:
                # 如果中途被封，休眠长一点
                wait_time = random.randint(60, 120)
                logger.error(f"❌ {symbol} 触发限流！强制休眠 {wait_time} 秒...")
                time.sleep(wait_time) 
            else:
                logger.error(f"❌ {symbol} 失败: {e}")
                time.sleep(1)

    logger.info("🏁 股票任务全部结束")