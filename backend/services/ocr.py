import numpy as np
import cv2
import easyocr

_reader = easyocr.Reader(["en"], gpu=False, verbose=False)


def extract_text(image_bytes: bytes) -> str:
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return ""

    results = _reader.readtext(img, detail=1)
    lines = [text for _, text, confidence in results if confidence > 0.4]
    return "\n".join(lines)
