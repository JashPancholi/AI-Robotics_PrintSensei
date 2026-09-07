import base64
import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException
from app.schemas.camera import CameraCaptureRequest, CameraCaptureResponse

camera_router = APIRouter(prefix="/camera", tags=["Camera"])

CAPTURES_DIR = Path("data/captures")
CAPTURES_DIR.mkdir(parents=True, exist_ok=True)


@camera_router.post("/capture", response_model=CameraCaptureResponse)
def save_captured_photo(payload: CameraCaptureRequest):
    try:
        raw_data = payload.image_data
        if "," in raw_data:
            _, encoded = raw_data.split(",", 1)
        else:
            encoded = raw_data

        image_bytes = base64.b64decode(encoded)
        filename = f"capture_{uuid.uuid4().hex[:8]}.jpg"
        file_path = CAPTURES_DIR / filename

        with open(file_path, "wb") as f:
            f.write(image_bytes)

        return CameraCaptureResponse(
            success=True,
            filename=filename,
            file_path=str(file_path.resolve()),
            relative_url=f"/captures/{filename}",
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to save captured photo: {str(exc)}")