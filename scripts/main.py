"""
统一入口模块
启动：【数据采集】+ 【数据查询 API】
"""
import schedule
import time
import sys
import logging
import os
import threading

# ============================================
# 【共享】数据库初始化
# ============================================
from scripts.database import init_db_environment, has_data

# ============================================
# 【采集】任务模块
# ============================================
# 【采集】股票模块（暂时屏蔽）
# from scripts.tasks.stocks import fetch_stock_data, check_yfinance_status

# 【采集】宏观模块
from scripts.tasks.macro import fetch_macro_data


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("quant.collector")


# ============================================
# 【API】服务
# ============================================
def _run_api_server(host: str = "0.0.0.0", port: int = 8000):
    """【API】FastAPI 服务（后台线程运行）"""
    import uvicorn
    from scripts.api.main import app
    uvicorn.run(app, host=host, port=port, log_level="warning")


def start_api(host: str = "0.0.0.0", port: int = 8000):
    """【API】启动 API 服务"""
    thread = threading.Thread(
        target=_run_api_server,
        args=(host, port),
        daemon=True
    )
    thread.start()
    logger.info(f"🌐 【API】http://{host}:{port}")


# ============================================
# 【采集】服务
# ============================================
def run_collector():
    """【采集】调度器主循环"""
    logger.info("🛡️ 【采集】调度器运行中...")
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except KeyboardInterrupt:
            logger.info("👋 服务停止")
            break
        except Exception as e:
            logger.error(f"❌ 采集异常: {e}")
            time.sleep(60)


def main():
    """
    统一入口：同时启动【采集】+【API】
    
    环境变量:
        API_HOST: API 地址 (默认: 0.0.0.0)
        API_PORT: API 端口 (默认: 8000)
    """
    logger.info(f"🚀 启动 | OpenBB v{os.getenv('OPENBB_VERSION', 'Unknown')}")
    
    # 初始化数据库
    init_db_environment()
    
    # ============================================
    # 【采集】初始数据检查与初始化
    # ============================================
    tables_to_check = [
        # 【采集】股票（暂时屏蔽）
        # ("market_stocks_daily", fetch_stock_data, "股票"),
        
        # 【采集】宏观指标
        ("macro_economic_data", fetch_macro_data, "宏观指标"),
    ]
    
    for table_name, fetch_func, desc in tables_to_check:
        if not has_data(table_name):
            logger.info(f"🆕 【采集】{desc}表无数据，执行首次采集...")
            try:
                fetch_func()
                logger.info(f"✅ 【采集】{desc}首次采集完成")
            except Exception as e:
                logger.error(f"❌ 【采集】{desc}首次采集失败: {e}")
        else:
            logger.info(f"✅ 【采集】{desc}表已有数据")
    
    # ============================================
    # 【采集】配置定时任务
    # ============================================
    # 【采集】股票定时任务（暂时屏蔽）
    # schedule.every().day.at("06:00").do(fetch_stock_data)
    
    # 【采集】宏观指标定时任务
    schedule.every().day.at("08:00").do(fetch_macro_data)
    
    logger.info("📅 【采集】定时任务:")
    for job in schedule.jobs:
        logger.info(f"   - {job}")
    
    # 【采集】网络检查（暂时屏蔽，因股票模块已屏蔽）
    # if check_yfinance_status():
    #     logger.info("✅ 【采集】网络正常")
    # else:
    #     logger.warning("⚠️ 【采集】网络异常")
    
    # ============================================
    # 【API】启动
    # ============================================
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    start_api(host, port)
    
    # ============================================
    # 【采集】启动（阻塞）
    # ============================================
    run_collector()


if __name__ == "__main__":
    main()
