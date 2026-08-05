import io
import os
import re
from pathlib import Path

import pydicom
from fastapi import FastAPI, File, HTTPException, UploadFile

app = FastAPI(
    title="PACS DICOM Router Gateway",
    description="Lightweight DICOM routing gateway that archives files by Modality.",
    version="0.1.0",
)

DATA_ROOT = Path(os.environ.get("DICOM_DATA_ROOT", "./data"))


def sanitize_modality(modality: str | None) -> str:
    """Normalize Modality; fall back to UNKNOWN when missing or invalid."""
    if not modality or not modality.strip():
        return "UNKNOWN"
    cleaned = re.sub(r"[^\w\-]", "", modality.strip().upper())
    return cleaned or "UNKNOWN"


def sanitize_filename(filename: str) -> str:
    """Keep only the basename to prevent path traversal."""
    name = Path(filename).name
    if not name or name in (".", ".."):
        raise HTTPException(status_code=400, detail="Invalid filename")
    return name


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for container orchestration and load balancers."""
    return {"status": "ok"}


@app.post("/api/router/upload")
async def upload_dicom(
    file: UploadFile = File(..., description="DICOM file to upload and route"),
) -> dict[str, str]:
    """
    Accept a DICOM file, read its Modality tag, and store it in the matching directory.

    Example: Modality=CT -> /data/CT/<filename>
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    safe_filename = sanitize_filename(file.filename)
    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        dataset = pydicom.dcmread(io.BytesIO(content))
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse DICOM file: {exc}",
        ) from exc

    modality = sanitize_modality(getattr(dataset, "Modality", None))
    target_dir = DATA_ROOT / modality
    target_dir.mkdir(parents=True, exist_ok=True)

    target_path = target_dir / safe_filename
    target_path.write_bytes(content)

    return {
        "message": "DICOM file archived successfully",
        "modality": modality,
        "path": str(target_path),
        "filename": safe_filename,
    }
