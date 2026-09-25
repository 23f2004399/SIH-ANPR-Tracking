from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.api.v1 import cameras, health, jobs
from backend.app.core import db
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.core.errors import (
    ApiError,
    api_error_handler,
    http_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # /health must answer even if the DB is unreachable — that split is the
    # whole point of having /ready separately, so a bad DB connection string
    # or a network blip at boot shouldn't take the process down.
    try:
        await db.connect()
    except Exception as e:
        print(f"[startup] DB connect failed, /ready will report unavailable: {e}")
    yield
    await db.disconnect()


app = FastAPI(title="ZyroTrace AI Backend", lifespan=lifespan)
app.add_exception_handler(ApiError, api_error_handler)
app.add_exception_handler(StarletteHTTPException, http_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)

app.include_router(health.router)
app.include_router(cameras.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
