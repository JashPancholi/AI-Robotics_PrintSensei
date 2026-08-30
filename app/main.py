from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import router
from app.startup import initialize_app
from shared.config import APP_NAME, APP_VERSION, CORS_ORIGINS

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)
app.include_router(router)
app.mount(
    "/generated-labels",
    StaticFiles(directory="generated_labels", check_dir=False),
    name="generated-labels",
)
app.mount(
    "/diagram-images",
    StaticFiles(directory="diagram_images", check_dir=False),
    name="diagram-images",
)


@app.on_event("startup")
def startup_event() -> None:
    initialize_app()
