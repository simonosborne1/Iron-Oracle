from fastapi import APIRouter, UploadFile, File, HTTPException
from models import ScanResponse
from cache import hash_image, set_cached_machine, log_scan
from services.vision import extract_plate

router = APIRouter()


@router.post("/api/scan", response_model=ScanResponse)
async def scan_plate(image: UploadFile = File(...)):
    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image")

    try:
        machine, raw_ocr = await extract_plate(image_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plate extraction failed: {e}")

    image_hash = hash_image(image_bytes)
    await set_cached_machine(image_hash, machine, raw_ocr)
    await log_scan(raw_ocr, machine, cached=False)
    return ScanResponse(machine=machine, cached=False, raw_ocr=raw_ocr)
