import qrcode
from PIL import Image, ImageTk

def _create_qr_core(booking_ref: str):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(booking_ref)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").get_image()

def generate_qr_image(booking_ref: str, size: int = 150) -> ImageTk.PhotoImage:
    img = _create_qr_core(booking_ref)
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(img)

def save_qr_to_file(booking_ref: str, output_path: str) -> str:
    img = _create_qr_core(booking_ref)
    img.save(output_path, "PNG")
    return output_path
