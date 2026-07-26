from fastapi import FastAPI
from app.routers import router
from app.startup import initialize_app
from shared.config import APP_NAME, APP_VERSION

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
)

app.include_router(router)


@app.on_event("startup")
def startup_event() -> None:
    initialize_app()
