# Quant Headless Collector - Deployment Guide

**版本**: 2.0.0
**日期**: 2025-02-05

## 1. 技术栈

- **Python**: 3.11
- **数据采集**: yfinance, OpenBB 4.6.0
- **数据库**: TimescaleDB 2.25.0 (PostgreSQL 18)
- **容器**: Docker, Docker Compose
- **依赖库**:
  - psycopg2-binary (PostgreSQL 连接)
  - sqlalchemy (ORM)
  - schedule (任务调度)
  - pandas (数据处理)

## 2. 容器配置

### 2.1 Dockerfile

**基础环境**:
- 镜像: `python:3.11-slim-bookworm`
- 工作目录: `/app`
- Python 路径: `/app`

**关键配置**:
```dockerfile
FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app"

ARG OPENBB_VERSION=4.6.0

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 build-essential && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    openbb==${OPENBB_VERSION} \
    psycopg2-binary \
    sqlalchemy \
    schedule \
    yfinance && \
    apt-get purge -y --auto-remove build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app/config

COPY ./scripts /app/scripts

CMD ["python", "/app/scripts/main.py"]
```

### 2.2 docker-compose.yml

**服务配置**:

**collector 服务**:
- 镜像: 本地构建
- 容器名: `quant_collector`
- 重启策略: `unless-stopped`
- 依赖: timescaledb (等待健康检查通过)
- 卷挂载:
  - `./scripts:/app/scripts` (代码热更新)
  - `./config:/app/config` (配置热更新)
- 环境变量:
  - `DB_HOST=timescaledb`
  - `DB_PORT=5432`
  - `DB_USER=postgres`
  - `DB_PASS=quant_password`
  - `DB_NAME=quant_data`
  - `OPENBB_VERSION=4.6.0`
  - `FRED_API_KEY=your_fred_api_key`
  - `TZ=Asia/Shanghai`
- 日志配置:
  - 驱动: json-file
  - 最大文件: 10MB
  - 保留文件: 3

**timescaledb 服务**:
- 镜像: `timescale/timescaledb:2.25.0-pg18`
- 容器名: `timescaledb_core`
- 重启策略: `unless-stopped`
- 共享内存: 1GB
- 卷挂载:
  - `./db_data:/var/lib/postgresql/data` (数据持久化)
- 环境变量:
  - `POSTGRES_USER=postgres`
  - `POSTGRES_PASSWORD=quant_password`
  - `POSTGRES_DB=quant_data`
  - `TZ=Asia/Shanghai`
- 端口映射: `5432:5432`
- 健康检查:
  - 命令: `pg_isready -U postgres`
  - 间隔: 10秒
  - 超时: 5秒
  - 重试: 5次
- 日志配置:
  - 驱动: json-file
  - 最大文件: 20MB
  - 保留文件: 3

**完整配置**:
```yaml
version: "3.8"

services:
  collector:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: quant_collector
    restart: unless-stopped
    depends_on:
      timescaledb:
        condition: service_healthy
    volumes:
      - ./scripts:/app/scripts
      - ./config:/app/config
    environment:
      - DB_HOST=timescaledb
      - DB_PORT=5432
      - DB_USER=postgres
      - DB_PASS=quant_password
      - DB_NAME=quant_data
      - OPENBB_VERSION=4.6.0
      - FRED_API_KEY=your_fred_api_key
      - TZ=Asia/Shanghai
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  timescaledb:
    image: timescale/timescaledb:2.25.0-pg18
    container_name: timescaledb_core
    restart: unless-stopped
    shm_size: 1g
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=quant_password
      - POSTGRES_DB=quant_data
      - TZ=Asia/Shanghai
    ports:
      - "5432:5432"
    volumes:
      - ./db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    logging:
      driver: "json-file"
      options:
        max-size: "20m"
        max-file: "3"
```

### 2.3 环境变量配置

**数据库配置**:
- `DB_HOST`: timescaledb
- `DB_PORT`: 5432
- `DB_USER`: postgres
- `DB_PASS`: quant_password
- `DB_NAME`: quant_data

**API 配置**:
- `FRED_API_KEY`: (必填，从 https://fred.stlouisfed.org/ 获取)

**时区配置**:
- `TZ`: Asia/Shanghai

**OpenBB 配置**:
- `OPENBB_VERSION`: 4.6.0

## 3. 部署指南

### 3.1 初始化与启动

**步骤**:

1. **准备配置文件**:
   - 创建 `config/stock_tickers.csv`
   - 每行一个股票代码
   - 示例:
     ```
     AAPL
     MSFT
     GOOGL
     TSLA
     NVDA
     ```

2. **准备 FRED API Key**:
   - 访问 https://fred.stlouisfed.org/
   - 注册账号并获取 API Key
   - 在 docker-compose.yml 中配置 `FRED_API_KEY`

3. **启动服务**:
   ```bash
   docker-compose up -d --build
   ```

4. **查看日志**:
   ```bash
   docker-compose logs -f collector
   ```

### 3.2 配置文件准备

**股票配置** (`config/stock_tickers.csv`):
- 格式: 无表头，每行一个股票代码
- 编码: UTF-8
- 示例:
  ```
  AAPL
  MSFT
  GOOGL
  AMZN
  META
  ```

**宏观配置** (`config/macro_series.csv`):
- 格式: 有表头 (series_id, description, provider)
- 编码: UTF-8
- 示例:
  ```
  series_id,description,provider
  CPIAUCSL,Consumer Price Index,fred
  GDP,Gross Domestic Product,fred
  UNRATE,Unemployment Rate,fred
  ```

### 3.3 服务验证

**检查容器状态**:
```bash
docker-compose ps
```

**检查启动日志**:
```bash
docker logs quant_collector
```

**验证数据库连接**:
```bash
docker exec -it timescaledb_core psql -U postgres -d quant_data -c "SELECT version();"
```

**验证数据表**:
```bash
docker exec -it timescaledb_core psql -U postgres -d quant_data -c "\dt"
```

**验证 TimescaleDB 扩展**:
```bash
docker exec -it timescaledb_core psql -U postgres -d quant_data -c "SELECT * FROM pg_extension WHERE extname = 'timescaledb';"
```

## 4. 使用指南

### 4.1 如何调整抓取列表

**股票配置**:
- 编辑 `config/stock_tickers.csv`
- 每行一个股票代码
- 示例:
  ```
  AAPL
  MSFT
  GOOGL
  TSLA
  NVDA
  META
  AMZN
  ```

**生效方式**:
- 方式 1: 重启容器 `docker-compose restart collector`
- 方式 2: 等待下次任务触发 (06:00)
- 无需重新构建镜像

### 4.2 如何扩展新模块

**步骤**:

1. **创建配置文件**:
   - 在 `config/` 目录下创建新配置文件
   - 示例: `config/crypto.csv`
   - 格式:
     ```
     BTC-USD
     ETH-USD
     DOGE-USD
     ```

2. **创建任务模块**:
   - 在 `scripts/tasks/` 下创建新模块
   - 示例: `scripts/tasks/crypto.py`
   - 参考现有模块结构

3. **实现功能**:
   - 实现 `fetch_crypto_data()` 函数
   - 使用 yfinance 获取加密货币数据
   - 保持批量下载和防封禁策略

4. **注册任务**:
   - 在 `scripts/main.py` 中导入
   - 添加调度规则:
     ```python
     from tasks.crypto import fetch_crypto_data
     schedule.every().hour.at(":00").do(fetch_crypto_data)
     ```

5. **重启容器**:
   ```bash
   docker-compose restart collector
   ```

### 4.3 常用命令

**启动服务**:
```bash
docker-compose up -d --build
```

**停止服务**:
```bash
docker-compose down
```

**重启服务**:
```bash
docker-compose restart
```

**查看日志**:
```bash
docker-compose logs -f collector
docker-compose logs -f timescaledb
```

**进入容器**:
```bash
docker-compose exec collector bash
docker-compose exec timescaledb_core bash
```

**查看容器状态**:
```bash
docker-compose ps
```

**查看数据库**:
```bash
docker exec -it timescaledb_core psql -U postgres -d quant_data
```

**备份数据库**:
```bash
docker exec timescaledb_core pg_dump -U postgres quant_data > backup_$(date +%Y%m%d).sql
```

**恢复数据库**:
```bash
docker exec -i timescaledb_core psql -U postgres quant_data < backup_20250205.sql
```

### 4.4 日志查看

**collector 日志**:
```bash
docker logs -f --tail 100 quant_collector
```

**timescaledb 日志**:
```bash
docker logs -f --tail 100 timescaledb_core
```

**日志级别**:
- INFO: 一般信息
- WARNING: 警告信息
- ERROR: 错误信息
- CRITICAL: 严重错误

**关键词搜索**:
```bash
docker logs quant_collector | grep "ERROR"
docker logs quant_collector | grep "入库成功"
```

## 5. 防封禁策略

### 5.1 设计目标

降低 yfinance IP 封禁风险，确保数据采集的稳定性和持续性。

### 5.2 策略概述

| 策略 | 实现方式 | 效果 |
|------|---------|------|
| 批量下载 | 每批 20 只股票 | 减少 95% 请求次数 |
| 单线程模式 | `threads=False` | 降低并发压力 |
| 批次间隔 | 10-20 秒随机休眠 | 避免请求密集 |
| 手动重试 | 3 次重试 + 递增延迟 | 应对网络波动 |
| 连接检查 | 启动前验证连接状态 | 快速失败 |

### 5.3 性能目标

假设采集 100 只股票:

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 请求次数 | 5 次 | 每批 20 只 |
| 总耗时 | < 90 秒 | 含批次间隔 |
| 封禁风险 | 极低 | 通过多重策略降低 |
| 启动时间 | < 5 秒 | 轻量级连接检查 |

### 5.4 故障排查

**问题**: 仍然出现 "Failed download"

**可能原因**:
- IP 被临时封禁
- 网络不稳定
- 代理配置错误

**解决方法**:
1. 增加批次间隔:
   ```python
   MIN_SLEEP = 15  # 从 10 改为 15
   MAX_SLEEP = 30  # 从 20 改为 30
   ```
2. 减少批次大小:
   ```python
   BATCH_SIZE = 10  # 从 20 改为 10
   ```
3. 增加重试次数:
   ```python
   RETRIES = 5  # 从 3 改为 5
   ```
4. 使用代理 IP

**问题**: FutureWarning

**可能原因**: 未显式设置 `auto_adjust`

**解决方法**: 确保代码中 `yf.download(..., auto_adjust=True)`

**问题**: 连接检查失败

**可能原因**:
- 网络不通
- 代理配置错误
- IP 被封

**解决方法**:
1. 检查网络连接
2. 检查代理配置
3. 等待一段时间后重试

**问题**: 容器无法启动

**可能原因**:
- 端口被占用
- 数据库连接失败
- 配置文件格式错误

**解决方法**:
1. 检查端口占用:
   ```bash
   netstat -tulpn | grep 5432
   ```
2. 查看容器日志:
   ```bash
   docker logs quant_collector
   docker logs timescaledb_core
   ```
3. 检查配置文件格式

**问题**: 数据库连接失败

**可能原因**:
- 数据库未就绪
- 密码错误
- 网络问题

**解决方法**:
1. 检查数据库健康状态:
   ```bash
   docker inspect timescaledb_core | grep -A 10 Health
   ```
2. 验证连接:
   ```bash
   docker exec -it timescaledb_core psql -U postgres -d quant_data
   ```
3. 检查环境变量配置

## 6. 交付物清单

### 6.1 配置文件

- [x] `config/stock_tickers.csv` - 股票代码配置
- [x] `config/macro_series.csv` - 宏观指标配置
- [x] `.gitignore` - Git 忽略规则 (包含 db_data/)

### 6.2 脚本文件

- [x] `scripts/main.py` - 调度器入口
- [x] `scripts/database.py` - 数据库工具
- [x] `scripts/tasks/stocks.py` - 股票采集模块
- [x] `scripts/tasks/macro.py` - 宏观采集模块
- [x] `scripts/tasks/__init__.py` - 任务模块初始化
- [x] `scripts/__init__.py` - 脚本模块初始化

### 6.3 Docker 文件

- [x] `Dockerfile` - 容器镜像定义
- [x] `docker-compose.yml` - 服务编排配置

### 6.4 文档文件

- [x] `docs/SPEC.md` - 功能需求文档
- [x] `docs/DEPLOYMENT.md` - 部署与技术文档
- [x] `README.md` - 项目说明

### 6.5 数据目录

- [x] `db_data/` - TimescaleDB 数据持久化目录 (Git 忽略)
