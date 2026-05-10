import base64
import json
import os
import anthropic
from models import TorqueSpec
from .pdf_extractor import PageContent

_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

TORQUE_KEYWORDS = {"torque", "ft-lb", "ft·lb", "lbf·ft", "n·m", "nm", "newton", "tighten", "ft. lb"}

SYSTEM_PROMPT = (
    "You are a heavy equipment service technician extracting torque specifications "
    "from service manuals. Be precise with values and units. "
    "Always respond with valid JSON only — no markdown, no explanation."
)

USER_PROMPT_TEMPLATE = """Extract all torque specifications from this service manual excerpt.
The machine is a {make} {model}.
Return a JSON array (empty array [] if none found):
[
  {{
    "component": "system or assembly name (e.g. Engine, Hydraulics, Drive Hub)",
    "fastener": "specific bolt/nut description",
    "torque_ftlb": number or null,
    "torque_ftlb_max": number or null,
    "torque_nm": number or null,
    "torque_nm_max": number or null,
    "notes": "lubrication, thread locker, sequence, or grade notes",
    "page_ref": page number or null
  }}
]
If a value appears in only one unit, convert to the other (1 ft-lb = 1.356 Nm).
Include min and max for ranges.

MANUAL EXCERPT:
{text}"""


def _is_torque_relevant(page: PageContent) -> bool:
    text_lower = (page.text or "").lower()
    return any(kw in text_lower for kw in TORQUE_KEYWORDS)


def _chunk_pages(pages: list[PageContent], size: int = 8) -> list[list[PageContent]]:
    return [pages[i:i + size] for i in range(0, len(pages), size)]


def _parse_specs(raw: str) -> list[TorqueSpec]:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    data = json.loads(text)
    if not isinstance(data, list):
        return []
    specs = []
    for item in data:
        try:
            specs.append(TorqueSpec(**item))
        except Exception:
            continue
    return specs


async def extract_torque(
    pages: list[PageContent], make: str, model: str, is_image_based: bool
) -> tuple[list[TorqueSpec], str]:
    relevant = [p for p in pages if _is_torque_relevant(p)] if not is_image_based else pages
    if not relevant:
        relevant = pages[:20]  # fallback: first 20 pages

    method = "vision" if is_image_based else "text"
    all_specs: list[TorqueSpec] = []
    seen: set[tuple] = set()

    for chunk in _chunk_pages(relevant):
        if is_image_based:
            chunk_specs = await _extract_from_images(chunk, make, model)
        else:
            chunk_specs = await _extract_from_text(chunk, make, model)

        for spec in chunk_specs:
            key = (spec.component.lower(), spec.fastener.lower())
            if key not in seen:
                seen.add(key)
                all_specs.append(spec)

    return all_specs, method


async def _extract_from_text(pages: list[PageContent], make: str, model: str) -> list[TorqueSpec]:
    combined = "\n\n".join(
        f"[Page {p.page_num}]\n{p.text}" for p in pages if p.text.strip()
    )
    if not combined.strip():
        return []

    response = _client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": USER_PROMPT_TEMPLATE.format(make=make, model=model, text=combined),
        }],
    )
    return _parse_specs(response.content[0].text)


async def _extract_from_images(pages: list[PageContent], make: str, model: str) -> list[TorqueSpec]:
    all_specs: list[TorqueSpec] = []
    for page in pages:
        if not page.image_bytes:
            continue
        b64 = base64.standard_b64encode(page.image_bytes).decode()
        response = _client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64}},
                    {"type": "text", "text": USER_PROMPT_TEMPLATE.format(
                        make=make, model=model, text=f"(image page {page.page_num})"
                    )},
                ],
            }],
        )
        all_specs.extend(_parse_specs(response.content[0].text))
    return all_specs
