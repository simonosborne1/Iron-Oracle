from pydantic import BaseModel


class MachineIdentity(BaseModel):
    make: str | None = None
    model: str | None = None
    serial_number: str | None = None
    year: int | None = None
    capacity: str | None = None
    voltage: str | None = None
    other_ids: dict | None = None
    confidence: float = 0.0
    notes: str | None = None


class ManualResult(BaseModel):
    title: str
    url: str
    manual_type: str  # "service" | "parts" | "operator" | "unknown"
    source: str       # "portal" | "serper"
    file_size_kb: int | None = None


class TorqueSpec(BaseModel):
    component: str
    fastener: str
    torque_ftlb: float | None = None
    torque_ftlb_max: float | None = None
    torque_nm: float | None = None
    torque_nm_max: float | None = None
    notes: str | None = None
    page_ref: int | None = None


class ScanResponse(BaseModel):
    machine: MachineIdentity
    cached: bool = False
    raw_ocr: str | None = None


class ManualsResponse(BaseModel):
    manuals: list[ManualResult]
    search_status: str  # "ok" | "no_results" | "error"
    cached: bool = False


class TorqueResponse(BaseModel):
    specs: list[TorqueSpec]
    extraction_method: str  # "text" | "vision" | "hybrid"
    spec_count: int
    cached: bool = False
