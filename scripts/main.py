import schedule
import time
import sys
import logging
import os

from scripts.database import init_db_environment
from scripts.tasks.stocks import fetch_stock_data, check_yfinance_status
from scripts.tasks.macro import fetch_macro_data

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("quant.scheduler")

def run_scheduler():
    logger.info(f"🚀 采集服务启动 | OpenBB v{os.getenv('OPENBB_VERSION', 'Unknown')}")
    
    init_db_environment()

    schedule.every().day.at("06:00").do(fetch_stock_data)
    schedule.every().day.at("08:00").do(fetch_macro_data)

    logger.info("📅 任务计划表:")
    for job in schedule.jobs:
        logger.info(f"   - {job}")

    logger.info("🔍 执行启动前网络连通性检查...")
    if check_yfinance_status():
        logger.info("✅ Yahoo Finance 连接正常，系统就绪。")
    else:
        logger.error("❌ Yahoo Finance 连接失败 (请检查网络/代理)，但调度器仍将继续运行。")

    logger.info("🛡️ 守护进程已启动，正在等待任务触发...")

    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except KeyboardInterrupt:
            logger.info("👋 服务已停止")
            break
        except Exception as e:
            logger.critical(f"❌ 调度器异常: {e}", exc_info=True)
            time.sleep(60)

if __name__ == "__main__":
    run_scheduler()
