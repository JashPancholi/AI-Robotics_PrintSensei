from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from shared.config import APP_NAME, APP_VERSION, MODE, HARDWARE_MODE

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def home():
    return f"""
    <html>
        <head><title>{APP_NAME}</title></head>
        <body style='font-family: Arial; margin: 2rem;'>
            <h1>PrintSensei is Running</h1>
            <p>Application: {APP_NAME}</p>
            <p>Version: {APP_VERSION}</p>
            <p>Mode: {MODE}</p>
            <p>Hardware: {HARDWARE_MODE}</p>
        </body>
    </html>
    """


@router.get("/health")
def health():
    return {
        "application": APP_NAME,
        "version": APP_VERSION,
        "mode": MODE,
        "hardware": HARDWARE_MODE,
        "status": "Running",
    }
