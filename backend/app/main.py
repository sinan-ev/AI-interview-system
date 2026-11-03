"""
FastAPI Main Application Entry Point.
Configures middleware, exception handlers, lifecycle events, and routes.
"""
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.router import api_router
from app.api.v1 import health
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import logger, request_id_ctx


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown events."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.ENVIRONMENT}]")
    try:
        from app.core.database import Base, engine
        import app.models  # register all models
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema verified and tables ready.")
    except Exception as e:
        logger.error(f"Error during schema initialization: {e}")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Assigns and propagates a unique correlation Request ID for each request."""

    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = req_id
        token = request_id_ctx.set(req_id)
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            process_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            response.headers["X-Request-ID"] = req_id
            response.headers["X-Process-Time-Ms"] = str(process_time_ms)
            logger.info(
                f"{request.method} {request.url.path} completed with {response.status_code}",
                extra={"latency_ms": process_time_ms, "status": response.status_code, "request_id": req_id}
            )
            return response
        finally:
            request_id_ctx.reset(token)


def create_application() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Production-grade AI Interview & Communication Assessment Platform Backend",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Middleware
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global Exception Handlers
    register_exception_handlers(app)

    # Root probes (for load balancers & container orchestrators)
    app.include_router(health.router, prefix="", tags=["Health"])

    # API v1 routes
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_application()
