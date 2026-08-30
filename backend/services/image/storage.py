import base64
import uuid
from pathlib import Path


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