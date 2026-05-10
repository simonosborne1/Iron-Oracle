from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from models import ManualsResponse
from cache import make_manual_cache_key, get_cached_manuals, set_cached_manuals
from services.manual_search import find_manuals

router = APIRouter()


class ManualsRequest(BaseModel):
    make: str
    model: str
    serial_number: str = ""


@router.post("/api/manuals", response_model=ManualsResponse)
async def get_manuals(req: ManualsRequest):
    if not req.make or not req.model:
        raise HTTPException(status_code=400, detail="make and model are required")

    cache_key = make_manual_cache_key(req.make, req.model, req.serial_number)

    cached = await get_cached_manuals(cache_key)
    if cached:
        results, status = cached
        return ManualsResponse(manuals=results, search_status=status, cached=True)

    try:
        results, status = await find_manuals(req.make, req.model, req.serial_number)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Manual search failed: {e}")

    await set_cached_manuals(cache_key, results, status)
    return ManualsResponse(manuals=results, search_status=status, cached=False)
