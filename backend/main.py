"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

from api.agent import router as agent_router
from api.auth import router as auth_router
from api.config import router as config_router
from api.dashboard import router as dashboard_router
from api.documents import router as documents_router
from utils.config import get_settings
from utils.logging_config import setup_logging
from utils.rate_limit import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger = logging.getLogger(__name__)
    settings = get_settings()
    logger.info("Backend started (log level=%s)", settings.LOG_LEVEL)
    yield
    logger.info("Backend shutting down")


app = FastAPI(title="Frontline Backend", version="0.14.0", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

settings = get_settings()
if settings.FRONTEND_URL == "*":
    origins = ["*"]
    allow_credentials = False
else:
    origins = [settings.FRONTEND_URL]
    allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router)
app.include_router(agent_router)
app.include_router(auth_router)
app.include_router(config_router)
app.include_router(dashboard_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
