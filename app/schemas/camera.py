from pydantic import BaseModel, Field


class CameraCaptureRequest(BaseModel):
    image_data: str = Field(
        ...,
        description="Base64 encoded image string or data URI (data:image/jpeg;base64,...)"
    )


class CameraCaptureResponse(BaseModel):
    success: bool
    filename: str
    file_path: str
    relative_url: str