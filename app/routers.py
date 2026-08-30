from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.api import history_router, public_shares_router, shares_router, study_router
from app.core.fake_request_generator import create_fake_print_request
from app.models.label_data import LabelData
from app.renderer import LabelRenderer
from app.schemas.render import RenderRequest, RenderResponse
from app.schemas.simulate import SimulateRequest, SimulateResponse
from shared.config import APP_NAME, APP_VERSION, MODE, HARDWARE_MODE

router = APIRouter()
router.include_router(study_router)
router.include_router(history_router)
router.include_router(shares_router)
router.include_router(public_shares_router)


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


@router.post("/simulate", response_model=SimulateResponse)
def simulate_print_request(payload: SimulateRequest):
    print_request, label_data = create_fake_print_request(payload.text)
    return SimulateResponse(
        request_id=print_request.request_id,
        intent=print_request.intent,
        status=print_request.status,
        label_type=label_data.label_type,
    )


@router.post("/render", response_model=RenderResponse)
def render_label(payload: RenderRequest):
    metadata = dict(payload.metadata)
    if payload.shelf is not None:
        metadata["shelf"] = payload.shelf

    label_data = LabelData(
        title=payload.title,
        subtitle=payload.subtitle,
        body=payload.body,
        quantity=payload.quantity,
        price=payload.price,
        date=payload.date,
        qr_data=payload.qr_data,
        template=payload.template,
        image_path=payload.image_path,
        label_type=payload.label_type,
        metadata=metadata,
    )
    result = LabelRenderer().render(label_data)
    return RenderResponse(
        status=result.status,
        file=result.file,
        width=result.width,
        height=result.height,
    )
