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

# API 版本前缀
API_PREFIX = "/api/v1"

# 注册路由（带版本前缀）
app.include_router(macro.router, prefix=f"{API_PREFIX}/macro", tags=["宏观数据"])
app.include_router(stocks.router, prefix=f"{API_PREFIX}/stocks", tags=["股票数据"])


@app.get("/")
async def root():
    """根路径重定向到文档"""
    return {
        "message": "Quant Data API",
        "docs": "/docs",
        "api_base": API_PREFIX,
        "endpoints": {
            "宏观数据": f"{API_PREFIX}/macro",
            "股票数据": f"{API_PREFIX}/stocks",
            "健康检查": f"{API_PREFIX}/health"
        }
    }


@app.get(f"{API_PREFIX}/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "api_version": "v1"}
