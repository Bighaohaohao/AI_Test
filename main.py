"""
AI 测试用例生成系统 - 主入口
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from database import create_tables
from routers import modules, requirements, test_cases, files, generate

# 创建 FastAPI 应用
app = FastAPI(
    title="AI 测试用例生成系统",
    description="基于 AI 的测试用例生成与管理平台",
    version="1.0.0"
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/exports", StaticFiles(directory="exports"), name="exports")

# 模板引擎
templates = Jinja2Templates(directory="templates")

# 注册路由
app.include_router(modules.router)
app.include_router(requirements.router)
app.include_router(test_cases.router)
app.include_router(files.router)
app.include_router(generate.router)


@app.on_event("startup")
async def startup_event():
    """应用启动时创建数据库表"""
    create_tables()
    print("数据库表创建完成")


# ==================== 页面路由 ====================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """首页 - 测试用例生成"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/test_cases.html", response_class=HTMLResponse)
async def test_cases_page(request: Request):
    """用例管理页面"""
    return templates.TemplateResponse("test_cases.html", {"request": request})


@app.get("/modules.html", response_class=HTMLResponse)
async def modules_page(request: Request):
    """功能模块管理页面"""
    return templates.TemplateResponse("modules.html", {"request": request})


@app.get("/api_config.html", response_class=HTMLResponse)
async def api_config_page(request: Request):
    """API密钥配置页面"""
    return templates.TemplateResponse("api_config.html", {"request": request})


# ==================== 主入口 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
