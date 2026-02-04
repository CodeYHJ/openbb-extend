import os
import sys
import logging
from sqlalchemy import create_engine, text

# 日志配置
logger = logging.getLogger("quant.db")

# 连接串
DB_URL = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

# 引擎 (连接池 Pre-ping 防止断连)
engine = create_engine(DB_URL, pool_pre_ping=True)

def get_engine():
    return engine

def init_db_environment():
    """初始化数据库环境"""
    try:
        with engine.connect() as conn:
            # 开启核心时序功能
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb;"))
            conn.commit()
        logger.info("✅ 数据库环境初始化完成 (TimescaleDB Ready)")
    except Exception as e:
        logger.critical(f"❌ 数据库初始化失败: {e}")
        sys.exit(1)

def ensure_hypertable(table_name, time_col='date'):
    """
    将表转换为超表 (Hypertable)
    """
    try:
        with engine.connect() as conn:
            # --- 核心修正点 ---
            # 增加 migrate_data => TRUE
            # 这样即使表里已经有数据了，TimescaleDB 也会帮我们把数据迁移到新的分区里
            query = text(f"""
                SELECT create_hypertable(
                    '{table_name}', 
                    '{time_col}', 
                    if_not_exists => TRUE, 
                    migrate_data => TRUE
                );
            """)
            conn.execute(query)
            conn.commit()
    except Exception as e:
        # 如果表已经是 Hypertable，或者有其他非致命错误，只打印警告
        # 很多时候 Warning 也是以 Exception 形式抛出的，需要过滤一下
        err_str = str(e)
        if "already a hypertable" in err_str:
            pass # 已经是了，忽略
        else:
            logger.warning(f"⚠️ Hypertable 检查 ({table_name}): {e}")