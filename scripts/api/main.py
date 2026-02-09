"""
数据读取 API 入口
仅提供查询功能，不提供写入/修改
"""
from fastapi import FastAPI
from contextlib import asynccontextmanager

from scripts.api.routers import macro, stocks


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时检查
    print("✅ API 服务启动")
    yield
    # 关闭时清理
    print("🛑 API 服务关闭")


app = FastAPI(
    title="Quant Data API",
    description="量化数据查询接口 - 仅提供读取功能",
    version="1.0.0",
    lifespan=lifespan
)

# 注册路由
app.include_router(macro.router, prefix="/macro", tags=["宏观数据"])
app.include_router(stocks.router, prefix="/stocks", tags=["股票数据"])


@app.get("/")
async def root():
    return {
        "message": "Quant Data API",
        "docs": "/docs",
        "endpoints": {
            "宏观数据": "/macro",
            "股票数据": "/stocks"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "ok"}
