from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.routers import router
from app.startup import initialize_app
from shared.config import APP_NAME, APP_VERSION

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
)

app.include_router(router)
Path("diagram_images").mkdir(exist_ok=True)
app.mount("/generated-images", StaticFiles(directory="diagram_images"), name="generated-images")


@app.on_event("startup")
def startup_event() -> None:
    initialize_app()
