import os
import sys
import logging
from sqlalchemy import create_engine, text

logger = logging.getLogger("quant.db")

DB_URL = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

engine = create_engine(DB_URL, pool_pre_ping=True)


def get_engine():
    return engine


def init_db_environment():
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb;"))
            conn.commit()
        logger.info("✅ 数据库环境初始化完成 (TimescaleDB 2.25.0-pg18)")
    except Exception as e:
        logger.critical(f"❌ 数据库初始化失败: {e}")
        sys.exit(1)


def ensure_hypertable(table_name, time_col='date'):
    try:
        with engine.connect() as conn:
            conn.execute(text(f"SELECT create_hypertable('{table_name}', '{time_col}', if_not_exists => TRUE);"))
            conn.commit()
    except Exception as e:
        logger.warning(f"⚠️ Hypertable 检查 ({table_name}): {e}")
