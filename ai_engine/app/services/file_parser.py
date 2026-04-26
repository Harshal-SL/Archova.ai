from pypdf import PdfReader
from PIL import Image
import pytesseract
import io
import os
from fastapi import HTTPException

# Point pytesseract to the default Tesseract install location on Windows.
# Download installer: https://github.com/UB-Mannheim/tesseract/wiki
_TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(_TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = _TESSERACT_PATH

async def parse_file(file) -> str:
    filename = file.filename.lower()

    # TEXT / MARKDOWN
    if filename.endswith(".txt") or filename.endswith(".md"):
        content = await file.read()
        return content.decode("utf-8", errors="replace")

    # PDF
    if filename.endswith(".pdf"):
        content = await file.read()
        reader = PdfReader(io.BytesIO(content))
        pages = []
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                pages.append(extracted)
        return "\n".join(pages)

    # IMAGE
    if filename.endswith((".png", ".jpg", ".jpeg")):
        content = await file.read()
        image = Image.open(io.BytesIO(content))
        try:
            return pytesseract.image_to_string(image)
        except pytesseract.TesseractNotFoundError:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Tesseract OCR is not installed. "
                    "Download and install it from: "
                    "https://github.com/UB-Mannheim/tesseract/wiki"
                )
            )

    return ""