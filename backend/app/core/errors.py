import uuid

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message


def envelope(data):
    return {"data": data, "meta": {"request_id": str(uuid.uuid4())}}


async def api_error_handler(request: Request, exc: ApiError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


async def http_error_handler(request: Request, exc: StarletteHTTPException):
    # Covers framework-raised errors (404 on an unmatched route, etc.) that
    # never reach the generic handler below since Starlette handles them first.
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "HTTP_ERROR", "message": str(exc.detail)}},
    )


async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "VALIDATION_ERROR", "message": str(exc.errors())}},
    )


async def unhandled_error_handler(request: Request, exc: Exception):
    # Anything that isn't a deliberate ApiError still needs the same envelope
    # shape — SOP section 5 says don't leak stack traces, so the real
    # exception goes to the server log, not the response.
    print(f"[unhandled] {type(exc).__name__}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "Something went wrong."}},
    )
