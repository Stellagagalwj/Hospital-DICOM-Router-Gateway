import io

import pydicom
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid


def make_minimal_dicom(modality: str = "CT", filename: str = "test.dcm") -> bytes:
    """生成最小可用的 DICOM 字节流，供测试使用。"""
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = generate_uid()
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

    dataset = FileDataset(
        filename,
        {},
        file_meta=file_meta,
        preamble=b"\0" * 128,
    )
    dataset.is_little_endian = True
    dataset.is_implicit_VR = False
    dataset.SOPClassUID = file_meta.MediaStorageSOPClassUID
    dataset.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    dataset.Modality = modality
    dataset.PatientName = "Test^Patient"

    buffer = io.BytesIO()
    dataset.save_as(buffer)
    return buffer.getvalue()
