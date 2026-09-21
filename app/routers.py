import base64
import binascii
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from fastapi.responses import HTMLResponse
from app.core.fake_request_generator import create_fake_print_request
from app.models.label_data import LabelData
from app.renderer import LabelRenderer
from app.schemas.render import RenderRequest, RenderResponse
from app.schemas.simulate import SimulateRequest, SimulateResponse
from backend.core.enums import TaskType
from backend.core.request import Request
from backend.engines.diagram.service import DiagramService
from shared.config import APP_NAME, APP_VERSION, MODE, HARDWARE_MODE

router = APIRouter()


class StudyGenerationRequest(BaseModel):
    """Dashboard payload for the Study-mode diagram generator."""

    prompt: str
    image_data: str | None = None
    detail_level: str = Field(default="medium", pattern="^(low|medium|high)$")


def _save_reference_image(image_data: str | None) -> Path | None:
    if not image_data:
        return None

    encoded = image_data.split(",", 1)[-1]
    try:
        image_bytes = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(status_code=422, detail="The reference image is not valid base64 data.") from exc

    uploads = Path("diagram_images/uploads")
    uploads.mkdir(parents=True, exist_ok=True)
    image_path = uploads / f"reference_{uuid.uuid4().hex[:8]}.png"
    image_path.write_bytes(image_bytes)
    return image_path


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


@router.post("/study/generate")
def generate_study_diagram(payload: StudyGenerationRequest):
    """Generate the same educational diagram used by backend/tests/test_image_generation.py."""
    prompt = payload.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=422, detail="Describe the diagram you want to generate.")

    try:
        reference_image = _save_reference_image(payload.image_data)
        result = DiagramService().generate(Request(
            task=TaskType.DIAGRAM,
            instruction=prompt,
            detail_level=payload.detail_level,
            image=reference_image,
            input_mode="camera+voice" if reference_image else "voice+text",
        ))
    except HTTPException:
        raise
    except Exception as exc:  # Keep provider details out of the browser response.
        raise HTTPException(status_code=502, detail="Image generation failed. Check your configured AI provider and try again.") from exc

    image = result.payload.get("image") if result.success else None
    if not image:
        raise HTTPException(status_code=502, detail="The image provider returned no image.")

    return {"image_url": f"/generated-images/{Path(image).name}", "prompt": result.payload.get("prompt", prompt)}
