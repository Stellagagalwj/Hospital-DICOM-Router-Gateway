import io

import pydicom
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid

from redaction import redact_dicom


def _make_dicom_with_phi() -> bytes:
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = generate_uid()
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

    dataset = FileDataset(
        "phi.dcm",
        {},
        file_meta=file_meta,
        preamble=b"\0" * 128,
    )
    dataset.is_little_endian = True
    dataset.is_implicit_VR = False
    dataset.SOPClassUID = file_meta.MediaStorageSOPClassUID
    dataset.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    dataset.Modality = "CT"
    dataset.PatientName = "Doe^John"
    dataset.PatientID = "P-12345"
    dataset.PatientBirthDate = "19800115"

    buffer = io.BytesIO()
    dataset.save_as(buffer)
    return buffer.getvalue()


def test_redact_dicom_blanks_phi_tags() -> None:
    original_bytes = _make_dicom_with_phi()
    original = pydicom.dcmread(io.BytesIO(original_bytes))

    sanitized = redact_dicom(original_bytes)

    assert sanitized.PatientName == "ANONYMOUS"
    assert sanitized.PatientID != ""
    assert sanitized.PatientBirthDate == ""
    assert sanitized.Modality == "CT"
    assert original.PatientName == "Doe^John"
    assert original.PatientID == "P-12345"
    assert original.PatientBirthDate == "19800115"


def test_redact_dicom_does_not_mutate_input_dataset() -> None:
    original = pydicom.dcmread(io.BytesIO(_make_dicom_with_phi()))

    sanitized = redact_dicom(original)

    assert sanitized is not original
    assert original.PatientName == "Doe^John"
    assert sanitized.PatientName == "ANONYMOUS"
