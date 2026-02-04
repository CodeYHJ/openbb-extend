FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # ⚠️【新增】关键修正：将 /app 加入 Python 搜索路径
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
    schedule && \
    apt-get purge -y --auto-remove build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app/config

COPY ./scripts /app/scripts

CMD ["python", "/app/scripts/main.py"]
