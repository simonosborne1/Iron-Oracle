import re
from difflib import SequenceMatcher
from models import MachineIdentity

KNOWN_MAKES = [
    "JLG", "GENIE", "SKYJACK", "HAULOTTE", "TEREX", "UPRIGHT", "SNORKEL",
    "TOYOTA", "CROWN", "RAYMOND", "YALE", "HYSTER", "CATERPILLAR", "CAT",
    "MANITOU", "LULL", "GRADALL", "BIL-JAX", "GROVE", "MERLO", "XTREME",
    "BOBCAT", "JCB", "LIEBHERR",
]

_MAKE_DISPLAY = {
    "CAT": "Caterpillar", "BIL-JAX": "Bil-Jax",
    "JLG": "JLG", "JCB": "JCB",
}

# Words that are plate field labels, never field values
_LABEL_WORDS = {
    "NUMBER", "NUMBERS", "UMBER", "YEAR", "CAPACITY", "WEIGHT", "NO", "NUM",
    "HEIGHT", "WIDTH", "LENGTH", "DATE", "TYPE", "CODE", "MODEL", "MDL",
    "SERIAL", "MANUFACTURE", "MANUFACTURED", "ONLY", "CHART", "INDUSTRIES",
    "EQUIPMENT", "INC", "LLC", "LTD", "MFG", "MFD",
}

# OCR commonly misreads digits as these letters — normalize for make matching
_DIGIT_TO_ALPHA = str.maketrans("01528", "OISBZ")

# Predominantly-numeric serial: normalize letters that look like digits
_ALPHA_TO_DIGIT = str.maketrans("OILSBZ", "011582")


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


# ---------------------------------------------------------------------------
# Make
# ---------------------------------------------------------------------------

def _find_make(lines: list[str]) -> str | None:
    # Pass 1: exact word boundary match
    for line in lines:
        for make in KNOWN_MAKES:
            if re.search(rf"(?<![A-Z0-9]){re.escape(make)}(?![A-Z0-9])", line):
                return _display_make(make)

    # Pass 2: fuzzy match — same token length, 80%+ similarity after OCR normalization
    for line in lines:
        tokens = re.findall(r"[A-Z0-9]{3,}", line)
        for token in tokens:
            for make in KNOWN_MAKES:
                if len(token) == len(make):
                    normalized = token.translate(_DIGIT_TO_ALPHA)
                    if SequenceMatcher(None, normalized, make).ratio() >= 0.80:
                        return _display_make(make)
    return None


def _display_make(make: str) -> str:
    return _MAKE_DISPLAY.get(make, make.title() if len(make) > 3 else make)


# ---------------------------------------------------------------------------
# Serial number
# ---------------------------------------------------------------------------

_SERIAL_LABELS = re.compile(
    r"^(?:SERIAL(?:\s*(?:NO?|NUMBER|NUM))?|SER(?:\s*NO?)?|S/?N)\s*[.:#/]?\s*",
    re.IGNORECASE,
)

def _find_serial(lines: list[str]) -> str | None:
    # Pass 1: label on same line as value ("SERIAL NO: 0300123456")
    for i, line in enumerate(lines):
        m = _SERIAL_LABELS.match(line)
        if m:
            remainder = line[m.end():].strip()
            val = re.match(r"([A-Z0-9][\w]{4,20})", remainder)
            if val and _is_value(val.group(1)):
                return _normalize_serial(val.group(1))

        # Pass 2: label on its own line, value on the next line
        if _SERIAL_LABELS.fullmatch(line.rstrip(".:#/ ")):
            val = _first_token(lines, i + 1)
            if val and any(c.isdigit() for c in val):
                return _normalize_serial(val)

    # Pass 3: fallback — long numeric sequence (7–12 digits)
    text_block = " ".join(lines)
    m = re.search(r"\b(\d{7,12})\b", text_block)
    if m:
        return m.group(1)
    return None


def _normalize_serial(serial: str) -> str:
    """In a predominantly-numeric serial, swap letters that look like digits."""
    digits = sum(c.isdigit() for c in serial)
    alphas = sum(c.isalpha() for c in serial)
    if digits > alphas:
        return serial.translate(_ALPHA_TO_DIGIT)
    return serial


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

_MODEL_LABELS = re.compile(
    r"^(?:MODEL|MOD(?:EL)?|MDL|TYPE)\s*[.:#/]?\s*",
    re.IGNORECASE,
)

# Patterns that look like standalone model numbers (no label needed)
_MODEL_STANDALONE = [
    r"^[A-Z]{1,4}-\d{2,4}[A-Z]{0,3}$",        # S-60, Z-62, GS-3232
    r"^[A-Z]{1,5}\d{2,4}[A-Z]{0,4}$",          # 450AJ, GS3232, E300AJP
    r"^[A-Z]{1,3}\d{2,4}[-/]\d{1,4}[A-Z]?$",  # Z-62/22, T40-170
    r"^[A-Z]{2,4}\s\d{2,4}[A-Z]{0,3}$",        # SJ 3219, GS 1932
    r"^\d{2,4}[A-Z]{2,5}$",                     # 450AJ, 860SJ
    r"^[A-Z]{2,4}\d{3,5}$",                     # HA16, SJ30, GS3246
    r"^[A-Z]\d{3,4}[A-Z]{2,4}$",               # M600J, S60HC
]

def _find_model(lines: list[str]) -> str | None:
    # Pass 1: label on same line ("MODEL: 450AJ")
    for i, line in enumerate(lines):
        m = _MODEL_LABELS.match(line)
        if m:
            remainder = line[m.end():].strip()
            val = re.match(r"([A-Z0-9][\w/.-]{1,20})", remainder)
            if val and _is_value(val.group(1)):
                return val.group(1)

        # Pass 2: label alone on one line, value on next
        if _MODEL_LABELS.fullmatch(line.rstrip(".:#/ ")):
            val = _first_token(lines, i + 1)
            if val and _is_value(val):
                return val

    # Pass 3: standalone model-number token
    for line in lines:
        clean = line.strip()
        for pattern in _MODEL_STANDALONE:
            if re.match(pattern, clean) and _is_value(clean):
                return clean
    return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_value(val: str) -> bool:
    return val.upper() not in _LABEL_WORDS and len(val) >= 2


def _first_token(lines: list[str], idx: int) -> str | None:
    if idx >= len(lines):
        return None
    m = re.match(r"([A-Z0-9][\w/.-]{1,25})", lines[idx].strip())
    return m.group(1) if m else None


def _find_year(lines: list[str]) -> int | None:
    text_block = " ".join(lines)
    m = re.search(r"(?:YEAR|MFG|MFD|MANUFACTURED|BUILD|DATE)\s*[:#]?\s*((?:19|20)\d{2})", text_block)
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
