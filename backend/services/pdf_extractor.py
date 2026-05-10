import io
import os
import httpx
import pdfplumber

PDF_MAX_BYTES = int(os.getenv("PDF_MAX_SIZE_MB", "50")) * 1024 * 1024
PDF_TIMEOUT = int(os.getenv("PDF_DOWNLOAD_TIMEOUT_SECONDS", "30"))


class PageContent:
    def __init__(self, page_num: int, text: str, image_bytes: bytes | None = None):
        self.page_num = page_num
        self.text = text
        self.image_bytes = image_bytes


async def download_pdf(url: str) -> bytes:
    async with httpx.AsyncClient(timeout=PDF_TIMEOUT, follow_redirects=True) as client:
        async with client.stream("GET", url) as resp:
            resp.raise_for_status()
            chunks = []
            total = 0
            async for chunk in resp.aiter_bytes(65536):
                total += len(chunk)
                if total > PDF_MAX_BYTES:
                    raise ValueError(f"PDF exceeds {os.getenv('PDF_MAX_SIZE_MB', 50)}MB limit")
                chunks.append(chunk)
            return b"".join(chunks)


def extract_pages(pdf_bytes: bytes) -> tuple[list[PageContent], bool]:
    """Returns (pages, is_image_based)."""
    pages: list[PageContent] = []

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            pages.append(PageContent(page_num=i + 1, text=text))

    total_chars = sum(len(p.text) for p in pages)
    avg_chars = total_chars / len(pages) if pages else 0
    is_image_based = avg_chars < 100

    if is_image_based:
        pages = _extract_as_images(pdf_bytes)

    return pages, is_image_based


def _extract_as_images(pdf_bytes: bytes) -> list[PageContent]:
    import fitz  # pymupdf
    pages: list[PageContent] = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        pages.append(PageContent(page_num=i + 1, text="", image_bytes=img_bytes))
    doc.close()
    return pages
