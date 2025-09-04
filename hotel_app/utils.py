import qrcode
from io import BytesIO
from django.core.files.base import ContentFile

def generate_qr_code(data: str, box_size: int = 10, border: int = 5, fill_color: str = "black", back_color: str = "white"):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=box_size,
        border=border,
    )

    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color=fill_color, back_color=back_color)

    buffer = BytesIO()
    img.save(buffer, format="PNG")

    image_value = buffer.getvalue()

    return ContentFile(image_value, name=f"{data}.png")
