from fastapi import FastAPI

from app.api.shares import public_router
from app.startup import initialize_app
from shared.config import APP_NAME, APP_VERSION

app = FastAPI(
    title=f"{APP_NAME} Public Shares",
    version=APP_VERSION,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.include_router(public_router)


@app.get("/health", include_in_schema=False)
def health() -> dict[str, str]:
    return {"status": "Running"}


@app.on_event("startup")
def startup_event() -> None:
    initialize_app()
