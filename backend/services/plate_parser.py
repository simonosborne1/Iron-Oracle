import re
from models import MachineIdentity

KNOWN_MAKES = [
    "JLG", "GENIE", "SKYJACK", "HAULOTTE", "TEREX", "UPRIGHT", "SNORKEL",
    "TOYOTA", "CROWN", "RAYMOND", "YALE", "HYSTER", "CATERPILLAR", "CAT",
    "MANITOU", "LULL", "GRADALL", "BIL-JAX", "GROVE", "MERLO", "XTREME",
]

_MAKE_DISPLAY = {"CAT": "Caterpillar", "BIL-JAX": "Bil-Jax", "JLG": "JLG"}

_LABEL_WORDS = {
    "NUMBER", "NUMBERS", "UMBER", "YEAR", "CAPACITY", "WEIGHT",
    "HEIGHT", "WIDTH", "LENGTH", "DATE", "TYPE", "CODE", "MODEL",
    "SERIAL", "MANUFACTURE", "MANUFACTURED", "ONLY", "CHART",
}


def parse_plate(raw_text: str) -> tuple[MachineIdentity, str]:
    upper = raw_text.upper()
    lines = [l.strip() for l in upper.splitlines() if l.strip()]

    make = _find_make(lines)
    model = _find_model(lines)
    serial = _find_serial(lines)
    year = _find_year(lines)
    capacity = _find_capacity(upper)
    voltage = _find_voltage(upper)

    filled = sum(x is not None for x in [make, model, serial, year])
    confidence = round(filled / 4.0, 2)

    machine = MachineIdentity(
        make=make,
        model=model,
        serial_number=serial,
        year=year,
        capacity=capacity,
        voltage=voltage,
        confidence=confidence,
        notes=f"OCR source text: {raw_text[:300]}",
    )
    return machine, raw_text


def _find_make(lines: list[str]) -> str | None:
    for line in lines:
        for make in KNOWN_MAKES:
            if re.search(rf"\b{re.escape(make)}\b", line):
                return _MAKE_DISPLAY.get(make, make.title() if len(make) > 3 else make)
    return None


def _is_label_word(val: str) -> bool:
    return val.upper() in _LABEL_WORDS


def _find_serial(lines: list[str]) -> str | None:
    text_block = " ".join(lines)
    patterns = [
        r"SERIAL\s+(?:N(?:\s*UMBER)?\s*)?[:#]?\s*([A-Z0-9]\w{4,20})",
        r"S/N\s*[:#]?\s*([A-Z0-9]\w{4,20})",
        r"SER\.?\s*N(?:O|R)?\.?\s*[:#]?\s*([A-Z0-9]\w{4,20})",
        r"\b(\d{7,12})\b",  # long numeric sequence — common for Skyjack and others
    ]
    for pattern in patterns:
        m = re.search(pattern, text_block)
        if m:
            val = m.group(1)
            if _is_label_word(val):
                continue
            if not any(c.isdigit() for c in val):
                continue
            return val
    return None


def _find_model(lines: list[str]) -> str | None:
    text_block = " ".join(lines)
    patterns = [
        r"MODEL\s*[:#]?\s*([A-Z0-9][\w/.-]{1,20})",
        r"MOD\.?\s*[:#]?\s*([A-Z0-9][\w/.-]{1,20})",
        r"TYPE\s*[:#]?\s*([A-Z0-9][\w/.-]{1,20})",
    ]
    for pattern in patterns:
        m = re.search(pattern, text_block)
        if m:
            val = m.group(1)
            if _is_label_word(val):
                continue
            return val
    # Standalone model-number token: letters then digits (e.g. 450AJ, S-60, GS3232)
    for line in lines:
        if re.match(r"^[A-Z]{1,5}[-]?\d{2,4}[A-Z]{0,3}$", line):
            return line
    return None


def _find_year(lines: list[str]) -> int | None:
    text_block = " ".join(lines)
    m = re.search(r"(?:YEAR|MFG|MANUFACTURED|BUILD|DATE)\s*[:#]?\s*((?:19|20)\d{2})", text_block)
    if m:
        return int(m.group(1))
    m = re.search(r"\b((?:19|20)\d{2})\b", text_block)
    if m:
        return int(m.group(1))
    return None


def _find_capacity(upper_text: str) -> str | None:
    m = re.search(r"(\d[\d,]*\s*(?:LBS?|KG|LB|POUNDS?))", upper_text)
    return m.group(1) if m else None


def _find_voltage(upper_text: str) -> str | None:
    m = re.search(r"(\d+\s*V(?:OLTS?)?)", upper_text)
    return m.group(1) if m else None
