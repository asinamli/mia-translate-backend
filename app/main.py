import time
from fastapi import FastAPI, Request

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

from fastapi.middleware.cors import CORSMiddleware

configure_logging()

settings = get_settings()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.app_name,
    description="FastAPI backend service for Mektup Mia-Translate model integration.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_http_requests(request: Request, call_next):
    start_time = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((time.perf_counter()- start_time) * 1000, 2)

        logger.exception(
            "HTTP request failed",
            extra={
                "request_id": request.headers.get("X-Request-ID"),
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration_ms,
            },
        )

        raise
    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    logger.info(
        "HTTP request completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response

app.include_router(health_router)
app.include_router(api_router, prefix=settings.api_prefix)