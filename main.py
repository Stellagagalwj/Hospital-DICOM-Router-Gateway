import os
import re
import sys
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from loguru import logger
from redaction import redact_dicom 

# --- 🚀 日志配置 (可观测性初始化) ---
# 清除原生配置，强制让所有日志以 JSON 格式输出到标准输出流 (stdout)
# 这样 Docker 容器或 AWS 极容易捕获并建立索引
logger.remove()
logger.add(sys.stdout, serialize=True, level="INFO")

app = FastAPI(
    title="PACS DICOM Router Gateway",
    description="Enterprise-grade DICOM routing gateway with GDPR-compliant PHI redaction and Audit Trails.",
    version="0.3.0",
)

DATA_ROOT = Path(os.environ.get("DICOM_DATA_ROOT", "./data"))

def sanitize_modality(modality: str | None) -> str:
    if not modality or not modality.strip():
        return "UNKNOWN"
    cleaned = re.sub(r"[^\w\-]", "", modality.strip().upper())
    return cleaned or "UNKNOWN"

def sanitize_filename(filename: str) -> str:
    name = Path(filename).name
    if not name or name in (".", ".."):
        logger.warning("Path traversal attempt detected", extra={"attempted_filename": filename})
        raise HTTPException(status_code=400, detail="Invalid filename")
    return name

@app.on_event("startup")
async def startup_event():
    logger.info("PACS Gateway starting up. Audit trail enabled.")

@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/api/router/upload")
async def upload_dicom(
    request: Request,
    file: UploadFile = File(..., description="DICOM file to upload, redact, and route"),
) -> dict:
    
    client_host = request.client.host if request.client else "unknown"
    
    # 1. 基础接收日志
    logger.info("Incoming DICOM upload request", extra={"client_ip": client_host, "filename": file.filename})

    if not file.filename:
        logger.error("Upload rejected: Missing filename", extra={"client_ip": client_host})
        raise HTTPException(status_code=400, detail="Filename is required")
    
    if not file.filename.endswith('.dcm'):
        logger.error("Upload rejected: Invalid format", extra={"client_ip": client_host, "filename": file.filename})
        raise HTTPException(status_code=400, detail="Invalid file format. Only .dcm accepted.")

    content = await file.read()
    file_size_kb = len(content) / 1024

    if not content:
        logger.error("Upload rejected: Empty file", extra={"client_ip": client_host})
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # 2. 脱敏处理与异常日志
    try:
        sanitized = redact_dicom(content)
        logger.debug("DICOM PHI redacted successfully", extra={"filename": file.filename})
    except Exception as exc:
        logger.exception("Failed to parse or redact DICOM file", extra={"error": str(exc), "filename": file.filename})
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse or redact DICOM file: {exc}",
        )

    # 3. 路由归档与审计追踪日志
    modality = sanitize_modality(getattr(sanitized, "Modality", None))
    target_dir = DATA_ROOT / modality
    target_dir.mkdir(parents=True, exist_ok=True) 

    target_path = target_dir / sanitize_filename(file.filename)
    sanitized.save_as(target_path)

    # 🌟 核心审计日志 (Audit Trail)
    logger.info(
        "DICOM successfully archived", 
        extra={
            "action": "ARCHIVE",
            "modality": modality,
            "sanitized_patient_id": sanitized.PatientID,
            "file_size_kb": round(file_size_kb, 2),
            "destination": str(target_path)
        }
    )

    return {
        "message": "DICOM file sanitized and archived successfully",
        "modality": modality,
        "sanitized_patient_id": sanitized.PatientID,
        "path": str(target_path),
        "filename": file.filename,
    }