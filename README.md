# Quant Headless Collector System

基于 OpenBB v4.6 的模块化、配置驱动型金融数据采集引擎。

## 项目简介

本项目构建一个单节点、无头模式的数据采集系统，通过 OpenBB 统一接口获取多资产类别（股票、宏观，未来可扩展加密货币等）数据，并持久化至 TimescaleDB。

**核心特性**：
- 配置驱动：采集内容由外部 CSV 文件控制
- 模块化：股票、宏观、加密货币各自独立为 Task 模块
- 技术锁定：OpenBB v4.6.0 + TimescaleDB 2.25.0-pg18

## 快速开始

### 1. 启动服务

```bash
docker-compose up -d --build
```

### 2. 查看日志

```bash
docker logs -f quant_collector
```

### 3. 连接数据库

使用数据库客户端（如 DBeaver）连接：
- Host: `localhost`
- Port: `5432`
- User: `postgres`
- Password: `quant_password`
- Database: `quant_data`

## 配置说明

### 股票配置 `config/stock_tickers.csv`

```csv
symbol,provider
AAPL,yfinance
MSFT,yfinance
GOOGL,yfinance
TSLA,yfinance
NVDA,yfinance
```

### 宏观指标配置 `config/macro_series.csv`

```csv
series_id,description,provider
CPIAUCSL,Consumer Price Index,fred
GDP,Gross Domestic Product,fred
UNRATE,Unemployment Rate,fred
```

## 如何调整采集列表？

直接编辑 `config/` 目录下的 CSV 文件，下次定时任务触发时（或重启容器后）自动生效。

```bash
# 重启容器应用新配置
docker restart quant_collector
```

## 扩展指南

### 添加加密货币数据源

1. 创建 `config/crypto.csv`：
```csv
symbol,provider
BTC-USD,yfinance
ETH-USD,yfinance
```

2. 创建 `scripts/tasks/crypto.py`：
```python
def fetch_crypto_data():
    # 读取配置并调用 OpenBB crypto 接口
    pass
```

3. 在 `scripts/main.py` 中添加调度规则：
```python
from tasks.crypto import fetch_crypto_data
schedule.every().hour.at(":00").do(fetch_crypto_data)
```

## 数据表结构

| 表名 | 描述 | 关键字段 | 更新频率 |
| --- | --- | --- | --- |
| `market_stocks_daily` | 股票日线 | `date`, `symbol`, `close`, `volume` | 每日 06:00 |
| `macro_economic_data` | 宏观指标 | `date`, `series_id`, `value` | 每日 08:00 |

## 管理命令

```bash
# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看容器状态
docker-compose ps

# 进入容器
docker-compose exec collector bash

# 查看数据库日志
docker logs -f timescaledb_core
```

## 技术栈

- **Python**: 3.11
- **OpenBB SDK**: v4.6.0
- **TimescaleDB**: 2.25.0 (PostgreSQL 18)
- **调度器**: schedule
- **ORM**: SQLAlchemy

## 许可证

遵循 OpenBB 项目的 AGPLv3 许可证。
