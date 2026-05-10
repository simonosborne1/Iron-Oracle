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

# Words that appear on plates as field labels, never as values
_LABEL_WORDS = {
    "NUMBER", "NUMBERS", "UMBER", "YEAR", "CAPACITY", "WEIGHT", "NO", "NUM",
    "HEIGHT", "WIDTH", "LENGTH", "DATE", "TYPE", "CODE", "MODEL", "MDL",
    "SERIAL", "MANUFACTURE", "MANUFACTURED", "ONLY", "CHART", "INDUSTRIES",
    "EQUIPMENT", "INC", "LLC", "LTD", "MFG", "MFD", "MAXIMUM", "MACHINE",
}

# Lines that are purely field labels (never contain values themselves)
_LABEL_LINE_RE = re.compile(
    r"^(?:MODEL|SERIAL|SER|S/?N|TYPE|MDL|YEAR|CAPACITY|WEIGHT|HEIGHT|WIDTH|"
    r"LENGTH|MAXIMUM|MFG|MFD)\b.*$",
    re.IGNORECASE,
)

# Digit → look-alike letter (for make fuzzy matching: OCR may read letters as digits)
# 0→O, 1→I, 5→S, 2→Z, 8→B
_DIGIT_TO_ALPHA = str.maketrans("01528", "OISZB")

# Letter → look-alike digit (for serial normalization in numeric-heavy strings)
# O→0, I→1, L→1, S→5, B→8, Z→2
_ALPHA_TO_DIGIT = str.maketrans("OILSBZ", "011582")

# Standalone model number patterns
_MODEL_PATTERNS = [
    r"^[A-Z]{1,4}-\d{2,4}[A-Z]{0,3}$",        # S-60, Z-62, GS-3232
    r"^[A-Z]{1,5}\d{2,4}[A-Z]{0,4}$",          # SJ1256THS, 450AJ, GS3232
    r"^[A-Z]{1,3}\d{2,4}[-/]\d{1,4}[A-Z]?$",  # Z-62/22, T40-170
    r"^[A-Z]{2,4}\s\d{2,4}[A-Z]{0,3}$",        # SJ 3219, GS 1932
    r"^\d{2,4}[A-Z]{2,5}$",                     # 860SJ, 40AJ
    r"^[A-Z]{2,4}\d{3,5}$",                     # HA16, SJ30, GS3246
    r"^[A-Z]\d{3,4}[A-Z]{2,4}$",               # M600J, S60HC
]


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

    # Pass 2: token-level fuzzy match (handles single-char OCR errors)
    # Normalize digits that look like letters before comparing
    for line in lines:
        tokens = re.findall(r"[A-Z0-9]{3,}", line)
        for token in tokens:
            normalized = token.translate(_DIGIT_TO_ALPHA)
            for make in KNOWN_MAKES:
                if len(normalized) == len(make):
                    ratio = SequenceMatcher(None, normalized, make).ratio()
                    if ratio >= 0.80:
                        return _display_make(make)
    return None


def _display_make(make: str) -> str:
    return _MAKE_DISPLAY.get(make, make.title() if len(make) > 3 else make)


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

_MODEL_LABEL_RE = re.compile(r"^(?:MODEL|MOD(?:EL)?|MDL|TYPE)\s*[.:#/]?\s*", re.IGNORECASE)

def _find_model(lines: list[str]) -> str | None:
    # Pass 1: inline label + value on same line ("MODEL: 450AJ")
    # Value must have at least one digit OR match a model shape — this rejects
    # OCR garble like "Model yex" where the OCR misread "Model year/number"
    for line in lines:
        m = _MODEL_LABEL_RE.match(line)
        if m:
            remainder = line[m.end():].strip()
            tok = re.match(r"([A-Z0-9][\w/.-]{1,20})", remainder)
            if tok and _is_value(tok.group(1)) and _is_plausible_model(tok.group(1)):
                return tok.group(1)

    # Pass 2: label on its own line — look at subsequent non-label lines for value
    for i, line in enumerate(lines):
        if _MODEL_LABEL_RE.fullmatch(line.rstrip(".:#/ ")) is None:
            continue
        val = _next_value(lines, i, _is_model_shaped)
        if val:
            return val

    # Pass 3: standalone model-shaped token anywhere on its own line
    for line in lines:
        clean = line.strip()
        if _is_model_shaped(clean) and _is_value(clean):
            return clean
    return None


def _is_model_shaped(val: str) -> bool:
    return any(re.match(p, val) for p in _MODEL_PATTERNS)


def _is_plausible_model(val: str) -> bool:
    """Model values extracted from a label must contain a digit or match a known shape.
    Rejects pure-letter OCR noise like 'YEX' (misread of 'year'/'number')."""
    return any(c.isdigit() for c in val) or _is_model_shaped(val)


# ---------------------------------------------------------------------------
# Serial number
# ---------------------------------------------------------------------------

_SERIAL_LABEL_RE = re.compile(
    r"^(?:SERIAL(?:\s*(?:NO?|NUMBER|NUM))?|SER(?:\s*NO?)?|S/?N)\s*[.:#/]?\s*",
    re.IGNORECASE,
)

def _find_serial(lines: list[str]) -> str | None:
    # Pass 1: inline label + value on same line ("SERIAL NO: 0300123456")
    for line in lines:
        m = _SERIAL_LABEL_RE.match(line)
        if m:
            remainder = line[m.end():].strip()
            tok = re.match(r"([A-Z0-9][\w]{4,20})", remainder)
            if tok and _is_serial_candidate(tok.group(1)):
                return _normalize_serial(tok.group(1))

    # Pass 2: label on its own line — look at subsequent non-label lines for a serial value
    # Serial values must have digits and must NOT look like a model number
    for i, line in enumerate(lines):
        if _SERIAL_LABEL_RE.fullmatch(line.rstrip(".:#/ ")) is None:
            continue
        val = _next_value(lines, i, _is_serial_candidate)
        if val:
            return _normalize_serial(val)

    # Pass 3: long numeric sequence (7–12 digits) — common for Skyjack, Crown, etc.
    text_block = " ".join(lines)
    m = re.search(r"\b(\d{7,12})\b", text_block)
    if m:
        return m.group(1)
    return None


def _is_serial_candidate(val: str) -> bool:
    """A serial must have digits, be a reasonable length, and not look like a model number."""
    if not any(c.isdigit() for c in val):
        return False
    if len(val) < 5:
        return False
    # If it's short AND model-shaped, it's probably a model, not a serial
    if len(val) <= 10 and _is_model_shaped(val):
        return False
    return True


def _normalize_serial(serial: str) -> str:
    """In predominantly-numeric serials, swap letters that look like digits."""
    digits = sum(c.isdigit() for c in serial)
    alphas = sum(c.isalpha() for c in serial)
    if digits > alphas:
        return serial.translate(_ALPHA_TO_DIGIT)
    return serial


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _next_value(lines: list[str], label_idx: int, validator) -> str | None:
    """Return the first token from lines after label_idx that passes validator,
    skipping any lines that are themselves field labels."""
    for j in range(label_idx + 1, min(label_idx + 5, len(lines))):
        candidate_line = lines[j].strip()
        if _LABEL_LINE_RE.match(candidate_line):
            continue  # this line is another label, skip it
        tok = re.match(r"([A-Z0-9][\w/.-]{1,25})", candidate_line)
        if tok and _is_value(tok.group(1)) and validator(tok.group(1)):
            return tok.group(1)
    return None


def _is_value(val: str) -> bool:
    return val.upper() not in _LABEL_WORDS and len(val) >= 2


def _is_label_line(line: str) -> bool:
    return bool(_LABEL_LINE_RE.match(line.strip()))


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
