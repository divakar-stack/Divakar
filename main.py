import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

import models
from config import BASE_DIR, COOKIE_SECURE, SECRET_KEY
from database import Base, engine
from routes import auth_routes, history_routes, page_routes, planner_routes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="PocketSmart AI", version="1.0.0", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, same_site="lax", https_only=COOKIE_SECURE)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.include_router(page_routes.router)
app.include_router(auth_routes.router)
app.include_router(planner_routes.router)
app.include_router(history_routes.router)


@app.exception_handler(404)
async def not_found(request: Request, _exc: Exception):
    return templates.TemplateResponse(request, "404.html", {"request": request}, status_code=404)


@app.exception_handler(Exception)
async def internal_error(request: Request, exc: Exception):
    logger.error("Unhandled request error: %s", type(exc).__name__)
    return templates.TemplateResponse(request, "500.html", {"request": request}, status_code=500)