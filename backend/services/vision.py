from models import MachineIdentity
from services.ocr import extract_text
from services.plate_parser import parse_plate


async def extract_plate(image_bytes: bytes) -> tuple[MachineIdentity, str]:
    raw_text = extract_text(image_bytes)
    return parse_plate(raw_text)
