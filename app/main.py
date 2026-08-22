"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import router as api_router
from app.config import settings
from app.logging_conf import configure_logging
from app.rate_limiter import limiter
from app.search import cse_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    yield
    await cse_client.aclose()


app = FastAPI(
    title="ICP Profile Discovery API",
    description=(
        "Discover people matching an Ideal Customer Profile across "
        "the public web (LinkedIn, X, company team pages, directories, "
        "personal sites, blogs). Powered by Google Custom Search JSON API."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_handler(request: Request, exc: RateLimitExceeded):
    return _rate_limit_exceeded_handler(request, exc)


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal error: {exc}"},
    )


app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=False,
        log_level=settings.log_level.lower(),
    )