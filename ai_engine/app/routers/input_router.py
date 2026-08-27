from fastapi import APIRouter, HTTPException, Request
from starlette.datastructures import UploadFile
from app.services.file_parser import parse_file
from app.services.prompt_builder import build_prompt

router = APIRouter(tags=["Input Processing"])

@router.post(
    "/api/input",
    openapi_extra={
        "requestBody": {
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Plain text requirement description"
                            },
                            "files": {
                                "type": "array",
                                "items": {"type": "string", "format": "binary"},
                                "description": "Upload .pdf, .docx, .txt, .md, .png, .jpg, .jpeg files"
                            }
                        }
                    }
                }
            },
            "required": False
        }
    }
)
async def process_input(request: Request):
    form = await request.form()

    text = form.get("text")
    # getlist handles both single and multiple file fields;
    # filter out empty strings sent by Swagger when no file is selected
    files = [f for f in form.getlist("files") if isinstance(f, UploadFile) and f.filename]

    if not text and not files:
        raise HTTPException(status_code=400, detail="No input provided. Send text and/or files.")

    text_blocks = []
    sources = []

    if text and text.strip():
        text_blocks.append(text.strip())
        sources.append("text")

    for f in files:
        parsed = await parse_file(f)
        if parsed.strip():
            text_blocks.append(parsed.strip())
            sources.append(f.filename)

    if not text_blocks:
        raise HTTPException(status_code=422, detail="Could not extract any text from the provided inputs.")

    combined_prompt = build_prompt(text_blocks)

    return {
        "combined_prompt": combined_prompt,
        "sources": sources,
        "block_count": len(text_blocks)
    }