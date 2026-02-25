from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.mappings import router as mappings_router
from app.api.metrics import router as metrics_router
from app.api.records import router as records_router
from app.core.config import settings

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        payload = {
            "code": exc.detail.get("code", "http_error"),
            "message": exc.detail.get("message", "Request failed"),
            "details": exc.detail.get("details"),
        }
    else:
        payload = {
            "code": "http_error",
            "message": str(exc.detail),
            "details": None,
        }
    return JSONResponse(status_code=exc.status_code, content=payload)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "code": "validation_error",
            "message": "Request validation failed",
            "details": {"errors": exc.errors()},
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "code": "internal_server_error",
            "message": "Unexpected server error",
            "details": {"error": str(exc)},
        },
    )


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(records_router, prefix=settings.api_prefix)
app.include_router(mappings_router, prefix=settings.api_prefix)
app.include_router(metrics_router, prefix=settings.api_prefix)
