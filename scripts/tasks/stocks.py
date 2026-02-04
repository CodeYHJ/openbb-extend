import pandas as pd
from openbb import obb
from scripts.database import get_engine, ensure_hypertable
import logging

logger = logging.getLogger("quant.task.stocks")


def fetch_stock_data():
    logger.info("🔄 开始股票采集任务...")

    try:
        stock_config = pd.read_csv('/app/config/stock_tickers.csv')

        if stock_config.empty:
            logger.warning("⚠️ 股票配置文件为空，跳过采集")
            return

        engine = get_engine()
        table_name = 'market_stocks_daily'

        for _, row in stock_config.iterrows():
            symbol = row['symbol']
            provider = row['provider']

            logger.info(f"📊 正在获取 {symbol} 数据 (provider: {provider})...")

            try:
                if provider == 'yfinance':
                    df = obb.equity.price.historical(symbol=symbol, provider="yfinance").to_dataframe()
                elif provider == 'polygon':
                    df = obb.equity.price.historical(symbol=symbol, provider="polygon").to_dataframe()
                else:
                    logger.warning(f"⚠️ 不支持的 provider: {provider}，跳过 {symbol}")
                    continue

                if df.empty:
                    logger.warning(f"⚠️ {symbol} 数据为空，跳过")
                    continue

                df.index.name = 'date'
                df.reset_index(inplace=True)
                df['date'] = pd.to_datetime(df['date'])
                df['symbol'] = symbol

                df.to_sql(table_name, engine, if_exists='append', index=False)

                logger.info(f"💾 {symbol} 数据入库成功 (Rows: {len(df)})")

            except Exception as e:
                logger.error(f"❌ {symbol} 采集失败: {e}")

        ensure_hypertable(table_name, 'date')
        logger.info("✅ 股票采集任务完成")

    except FileNotFoundError:
        logger.error("❌ 配置文件 /app/config/stock_tickers.csv 不存在")
    except Exception as e:
        logger.error(f"❌ 股票采集任务失败: {e}")
