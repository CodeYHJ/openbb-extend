import schedule
import time
import sys
import logging
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import init_db_environment
from tasks.stocks import fetch_stock_data
from tasks.macro import fetch_macro_data

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("quant.scheduler")


def run_scheduler():
    logger.info(f"🚀 采集服务启动 | OpenBB v{os.getenv('OPENBB_VERSION')}")

    time.sleep(2)

    init_db_environment()

    schedule.every().day.at("06:00").do(fetch_stock_data)
    schedule.every().day.at("08:00").do(fetch_macro_data)

    logger.info("⚡ 执行启动自检...")
    fetch_stock_data()
    fetch_macro_data()

    logger.info("📅 调度器就绪，进入守护模式...")

    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.critical(f"❌ 主循环异常: {e}")
            time.sleep(60)


if __name__ == "__main__":
    run_scheduler()
