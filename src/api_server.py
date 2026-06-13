"""
api_server.py —> FastAPI wrapper
POST /parse-resume  →  upload a file, get structured JSON back
Run -> uvicorn api_server:app --reload
"""

import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from src.resume_parser import parse_resume


app = FastAPI(title="Resume Parser API", version="1.0.0")
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".jpg", ".jpeg", ".png", ".tiff", ".tif"}


@app.post("/parse-resume")
async def parse_resume_endpoint(file: UploadFile = File(...)):
    """
    Upload a resume file (PDF / DOCX / image).
    Returns JSON with name, email, phone, location, top_skill.
    """
    suffix = Path(file.filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{suffix}'. "
            f"Allowed: {', '.join(SUPPORTED_EXTENSIONS)}",
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        temp_path = tmp.name

    try:
        result = parse_resume(temp_path)
        result.pop("_raw_text", None)  # don't send raw text over the wire
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        Path(temp_path).unlink(missing_ok=True)


@app.get("/health")
def health():
    return {"status": "ok"}
