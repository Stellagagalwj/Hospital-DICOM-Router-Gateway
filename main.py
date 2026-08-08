import os
import re
import sys
import io
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from loguru import logger
from redaction import redact_dicom 

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# --- ☁️ 环境与云端配置 ---
load_dotenv()

# 全局初始化 S3 客户端，让测试框架能够精准识别并 Mock 它
AWS_BUCKET = os.getenv("S3_BUCKET_NAME", "default-bucket")
s3_client = boto3.client(
    's3',
    region_name=os.getenv("AWS_REGION", "eu-north-1")
)

# --- 🚀 日志配置 (可观测性初始化) ---
logger.remove()
logger.add(sys.stdout, serialize=True, level="INFO")

app = FastAPI(
    title="PACS DICOM Router Gateway (Cloud Edition)",
    description="Enterprise-grade DICOM routing gateway with GDPR redaction, Audit Trails, and S3 Integration.",
    version="0.4.0",
)

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
    logger.info("PACS Gateway (Cloud Edition) starting up. Audit trail enabled.")

@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/api/router/upload")
async def upload_dicom(
    request: Request,
    file: UploadFile = File(..., description="DICOM file to upload, redact, and route"),
) -> dict:
    
    client_host = request.client.host if request.client else "unknown"
    
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

    # 1. 脱敏处理
    try:
        sanitized = redact_dicom(content)
        logger.debug("DICOM PHI redacted successfully", extra={"filename": file.filename})
    except Exception as exc:
        logger.exception("Failed to parse or redact DICOM file", extra={"error": str(exc), "filename": file.filename})
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse or redact DICOM file: {exc}",
        )

    # 2. 准备 S3 云端路径
    modality = sanitize_modality(getattr(sanitized, "Modality", None))
    safe_filename = sanitize_filename(file.filename)
    s3_key = f"{modality}/{safe_filename}"  # 比如 CT/sample_ct.dcm

    # 3. ☁️ 内存直传 AWS S3 (不再保存到本地磁盘)
    try:
        dicom_buffer = io.BytesIO()
        sanitized.save_as(dicom_buffer)
        dicom_buffer.seek(0)

        s3_client.upload_fileobj(dicom_buffer, AWS_BUCKET, s3_key)
        
        # S3 上传成功的审计日志
        logger.info(
            "DICOM securely archived to AWS S3", 
            extra={
                "action": "CLOUD_ARCHIVE",
                "modality": modality,
                "sanitized_patient_id": sanitized.PatientID,
                "s3_bucket": AWS_BUCKET,
                "s3_key": s3_key,
                "file_size_kb": round(file_size_kb, 2)
            }
        )
    except ClientError as e:
        logger.error("AWS S3 Upload Failed", extra={"error": str(e), "s3_key": s3_key})
        raise HTTPException(status_code=500, detail="Internal Cloud Storage Error")

    return {
        "message": "DICOM file sanitized and securely routed to Cloud",
        "modality": modality,
        "sanitized_patient_id": sanitized.PatientID,
        "cloud_location": f"s3://{AWS_BUCKET}/{s3_key}",
        "filename": file.filename,
    }