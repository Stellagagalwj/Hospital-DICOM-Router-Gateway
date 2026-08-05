"""GDPR-oriented PHI redaction helpers for DICOM datasets."""

from __future__ import annotations

import hashlib
import io
from copy import deepcopy
from pathlib import Path
from typing import BinaryIO

import pydicom
from pydicom.dataset import FileDataset

def _load_dataset(source: str | Path | bytes | BinaryIO | FileDataset) -> FileDataset:
    """Helper: 统一加载不同来源的 DICOM 数据"""
    if isinstance(source, FileDataset):
        # 确保传入已有 dataset 时返回深拷贝，防止污染原数据
        return deepcopy(source)
    if isinstance(source, (str, Path)):
        return pydicom.dcmread(source)
    if isinstance(source, bytes):
        return pydicom.dcmread(io.BytesIO(source))
    if hasattr(source, "read"):
        return pydicom.dcmread(source)

    raise TypeError(
        "source must be a file path, bytes, binary stream, or pydicom FileDataset"
    )

def redact_dicom(dicom_input: str | Path | bytes | BinaryIO | FileDataset) -> FileDataset:
    """
    接受文件路径、字节流或 FileDataset，返回脱敏后的 DICOM dataset 副本。
    保持原始数据集不变，实现 GDPR 合规的假名化与匿名化。
    """
    # 1. 统一数据加载管道 (调用下方的 helper 函数)
    dataset = _load_dataset(dicom_input)
    
    # 2. 单向哈希处理 PatientID (假名化 Pseudonymization)
    if "PatientID" in dataset and dataset.PatientID:
        original_id = str(dataset.PatientID).encode('utf-8')
        hashed_id = hashlib.sha256(original_id).hexdigest()[:16] 
        dataset.PatientID = hashed_id
        
    # 3. 清空或替换敏感明文信息 (匿名化 Anonymization)
    if "PatientName" in dataset:
        dataset.PatientName = "ANONYMOUS"
    if "PatientBirthDate" in dataset:
        dataset.PatientBirthDate = ""
        
    return dataset