from pathlib import Path

import pydicom
import pytest
from fastapi.testclient import TestClient

import main
from tests.conftest import make_minimal_dicom


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """使用临时目录作为 DICOM 存储根目录。"""
    monkeypatch.setenv("DICOM_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(main, "DATA_ROOT", tmp_path)
    return TestClient(main.app)


def test_upload_routes_ct_to_modality_folder(client: TestClient, tmp_path: Path) -> None:
    dicom_bytes = make_minimal_dicom(modality="CT")

    response = client.post(
        "/api/router/upload",
        files={"file": ("sample_ct.dcm", dicom_bytes, "application/dicom")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["modality"] == "CT"
    assert body["filename"] == "sample_ct.dcm"
    assert body["path"] == str(tmp_path / "CT" / "sample_ct.dcm")

    saved_file = tmp_path / "CT" / "sample_ct.dcm"
    assert saved_file.exists()

    saved_dataset = pydicom.dcmread(saved_file)
    assert saved_dataset.Modality == "CT"
    assert saved_dataset.PatientName == ""
    assert saved_dataset.PatientID == ""
    assert saved_dataset.PatientBirthDate == ""


def test_upload_rejects_invalid_dicom(client: TestClient) -> None:
    response = client.post(
        "/api/router/upload",
        files={"file": ("bad.dcm", b"not-a-dicom-file", "application/dicom")},
    )

    assert response.status_code == 400
    assert "Failed to parse DICOM file" in response.json()["detail"]
