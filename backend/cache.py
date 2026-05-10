import hashlib
import json
from database import get_db
from models import MachineIdentity, ManualResult, TorqueSpec


def hash_image(image_bytes: bytes) -> str:
    return hashlib.sha256(image_bytes).hexdigest()


def make_manual_cache_key(make: str, model: str, serial: str) -> str:
    parts = [s.lower().strip() for s in (make or "", model or "", serial or "")]
    return "|".join(parts)


async def get_cached_machine(image_hash: str) -> MachineIdentity | None:
    async with get_db() as db:
        row = await db.execute_fetchall(
            "SELECT * FROM machine_cache WHERE image_hash = ?", (image_hash,)
        )
        if not row:
            return None
        r = row[0]
        return MachineIdentity(
            make=r["make"], model=r["model"], serial_number=r["serial_number"],
            year=r["year"], capacity=r["capacity"], voltage=r["voltage"],
            other_ids=json.loads(r["other_ids"]) if r["other_ids"] else None,
            confidence=r["confidence"] or 0.0, notes=r["notes"],
        )


async def set_cached_machine(image_hash: str, machine: MachineIdentity, raw: str):
    async with get_db() as db:
        await db.execute(
            """INSERT OR REPLACE INTO machine_cache
               (image_hash, make, model, serial_number, year, capacity, voltage,
                other_ids, confidence, notes, raw_response)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (image_hash, machine.make, machine.model, machine.serial_number,
             machine.year, machine.capacity, machine.voltage,
             json.dumps(machine.other_ids) if machine.other_ids else None,
             machine.confidence, machine.notes, raw),
        )
        await db.commit()


async def get_cached_manuals(cache_key: str) -> tuple[list[ManualResult], str] | None:
    async with get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT * FROM manual_cache WHERE cache_key = ? AND expires_at > datetime('now')",
            (cache_key,),
        )
        if not rows:
            return None
        r = rows[0]
        results = [ManualResult(**m) for m in json.loads(r["results_json"])]
        return results, r["search_status"]


async def set_cached_manuals(cache_key: str, results: list[ManualResult], status: str):
    async with get_db() as db:
        await db.execute(
            """INSERT OR REPLACE INTO manual_cache
               (cache_key, results_json, result_count, search_status)
               VALUES (?,?,?,?)""",
            (cache_key, json.dumps([m.model_dump() for m in results]), len(results), status),
        )
        await db.commit()


async def log_scan(raw_ocr: str, machine: MachineIdentity, cached: bool = False):
    async with get_db() as db:
        await db.execute(
            """INSERT INTO scan_log (raw_ocr, make, model, serial_number, year, confidence, cached)
               VALUES (?,?,?,?,?,?,?)""",
            (raw_ocr, machine.make, machine.model, machine.serial_number,
             machine.year, machine.confidence, int(cached)),
        )
        await db.commit()


async def get_cached_torque(manual_url: str) -> tuple[list[TorqueSpec], str] | None:
    async with get_db() as db:
        rows = await db.execute_fetchall(
            "SELECT * FROM torque_cache WHERE manual_url = ? AND expires_at > datetime('now')",
            (manual_url,),
        )
        if not rows:
            return None
        r = rows[0]
        specs = [TorqueSpec(**s) for s in json.loads(r["specs_json"])]
        return specs, r["extraction_method"]


async def set_cached_torque(
    manual_url: str, make: str, model: str,
    specs: list[TorqueSpec], method: str, page_count: int,
):
    async with get_db() as db:
        await db.execute(
            """INSERT OR REPLACE INTO torque_cache
               (manual_url, make, model, specs_json, spec_count, pdf_page_count, extraction_method)
               VALUES (?,?,?,?,?,?,?)""",
            (manual_url, make, model,
             json.dumps([s.model_dump() for s in specs]), len(specs), page_count, method),
        )
        await db.commit()
