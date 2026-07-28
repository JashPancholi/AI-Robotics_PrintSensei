from PIL import Image
import qrcode


def generate_qr_image(data: str, size: int = 120) -> Image.Image:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white").convert("1")
    return image.resize((size, size), Image.Resampling.NEAREST)
