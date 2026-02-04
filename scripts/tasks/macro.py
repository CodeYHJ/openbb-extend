import pandas as pd
from openbb import obb
from scripts.database import get_engine, ensure_hypertable
import logging

logger = logging.getLogger("quant.task.macro")


def fetch_macro_data():
    logger.info("🔄 开始宏观指标采集任务...")

    try:
        macro_config = pd.read_csv('/app/config/macro_series.csv')

        if macro_config.empty:
            logger.warning("⚠️ 宏观指标配置文件为空，跳过采集")
            return

        engine = get_engine()
        table_name = 'macro_economic_data'

        for _, row in macro_config.iterrows():
            series_id = row['series_id']
            description = row['description']
            provider = row['provider']

            logger.info(f"📊 正在获取 {series_id} ({description}) 数据 (provider: {provider})...")

            try:
                if provider == 'fred':
                    if series_id == 'CPIAUCSL':
                        df = obb.economy.cpi(country="united_states", provider="fred").to_dataframe()
                    elif series_id == 'GDP':
                        df = obb.economy.gdp(country="united_states", provider="fred").to_dataframe()
                    elif series_id == 'UNRATE':
                        df = obb.economy.unemployment_rate(country="united_states", provider="fred").to_dataframe()
                    else:
                        logger.warning(f"⚠️ 暂不支持 {series_id}，跳过")
                        continue
                else:
                    logger.warning(f"⚠️ 不支持的 provider: {provider}，跳过 {series_id}")
                    continue

                if df.empty:
                    logger.warning(f"⚠️ {series_id} 数据为空，跳过")
                    continue

                df.index.name = 'date'
                df.reset_index(inplace=True)
                df['date'] = pd.to_datetime(df['date'])
                df['series_id'] = series_id
                df['description'] = description

                df.to_sql(table_name, engine, if_exists='append', index=False)

                logger.info(f"💾 {series_id} 数据入库成功 (Rows: {len(df)})")

            except Exception as e:
                logger.error(f"❌ {series_id} 采集失败: {e}")

        ensure_hypertable(table_name, 'date')
        logger.info("✅ 宏观指标采集任务完成")

    except FileNotFoundError:
        logger.error("❌ 配置文件 /app/config/macro_series.csv 不存在")
    except Exception as e:
        logger.error(f"❌ 宏观指标采集任务失败: {e}")
