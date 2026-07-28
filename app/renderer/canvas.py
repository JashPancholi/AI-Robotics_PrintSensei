from PIL import Image, ImageDraw


class LabelCanvas:
    def __init__(
        self,
        width: int = 384,
        height: int = 240,
        background: str = "white",
        margin: int = 18,
    ) -> None:
        self.width = width
        self.height = height
        self.background = background
        self.margin = margin

    def create(self) -> tuple[Image.Image, ImageDraw.ImageDraw]:
        image = Image.new("1", (self.width, self.height), self.background)
        return image, ImageDraw.Draw(image)
