import base64
import uuid
from pathlib import Path

import httpx


class ImageStorage:


    def __init__(self):

        self.output_dir = Path(
            "diagram_images"
        )

        self.output_dir.mkdir(
            exist_ok=True
        )


    def save_base64(
        self,
        image_data: str,
        prefix: str = "diagram"
    ):

        filename = (
            f"{prefix}_"
            f"{uuid.uuid4().hex[:8]}"
            ".png"
        )


        filepath = (
            self.output_dir /
            filename
        )


        image_bytes = base64.b64decode(
            image_data
        )


        with open(
            filepath,
            "wb"
        ) as file:

            file.write(
                image_bytes
            )


        return filepath

    def save_url(
        self,
        url: str,
        prefix: str = "diagram",
        timeout: float = 60.0,
    ):

        filename = (
            f"{prefix}_"
            f"{uuid.uuid4().hex[:8]}"
            ".png"
        )

        filepath = (
            self.output_dir /
            filename
        )

        with httpx.stream("GET", url, timeout=timeout) as response:
            response.raise_for_status()
            with open(filepath, "wb") as file:
                for chunk in response.iter_bytes():
                    file.write(chunk)

        return filepath