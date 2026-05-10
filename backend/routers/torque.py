from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from models import TorqueResponse
from cache import get_cached_torque, set_cached_torque
from services.pdf_extractor import download_pdf, extract_pages
from services.torque_analyzer import extract_torque

router = APIRouter()


class TorqueRequest(BaseModel):
    manual_url: str
    make: str = ""
    model: str = ""


@router.post("/api/torque", response_model=TorqueResponse)
async def get_torque(req: TorqueRequest):
    if not req.manual_url:
        raise HTTPException(status_code=400, detail="manual_url is required")

    cached = await get_cached_torque(req.manual_url)
    if cached:
        specs, method = cached
        return TorqueResponse(specs=specs, extraction_method=method, spec_count=len(specs), cached=True)

    try:
        pdf_bytes = await download_pdf(req.manual_url)
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to download PDF: {e}")

    try:
        pages, is_image_based = extract_pages(pdf_bytes)
        specs, method = await extract_torque(pages, req.make, req.model, is_image_based)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Torque extraction failed: {e}")

    await set_cached_torque(req.manual_url, req.make, req.model, specs, method, len(pages))
    return TorqueResponse(specs=specs, extraction_method=method, spec_count=len(specs), cached=False)
