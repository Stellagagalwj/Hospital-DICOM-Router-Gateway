from pathlib import Path
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

import main
from tests.conftest import make_minimal_dicom

@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """初始化测试客户端，并注入假的云端环境变量"""
    monkeypatch.setenv("S3_BUCKET_NAME", "mock-bucket-for-testing")
    monkeypatch.setenv("AWS_REGION", "eu-north-1")
    return TestClient(main.app)

# 🌟 核心修复：把 main 里的 s3_client 替换成替身 (Mock)
@patch("main.s3_client")
def test_upload_routes_ct_to_s3(mock_s3, client: TestClient) -> None:
    # 告诉替身：假装上传成功，什么都不用做
    mock_s3.upload_fileobj.return_value = None

    dicom_bytes = make_minimal_dicom(modality="CT")

    response = client.post(
        "/api/router/upload",
        files={"file": ("sample_ct.dcm", dicom_bytes, "application/dicom")},
    )

    # 1. 验证接口是否成功返回
    assert response.status_code == 200
    body = response.json()
    
    # 2. 验证新架构下的返回值 (云端路径)
    assert body["modality"] == "CT"
    assert "s3://mock-bucket-for-testing/CT/sample_ct.dcm" in body["cloud_location"]

    # 3. 🌟 终极验证：确认代码真的触发了 S3 上传动作！
    mock_s3.upload_fileobj.assert_called_once()

def test_upload_rejects_invalid_dicom(client: TestClient) -> None:
    response = client.post(
        "/api/router/upload",
        files={"file": ("bad.dcm", b"not-a-dicom-file", "application/dicom")},
    )

    assert response.status_code == 400
    assert "failed" in response.json()["detail"].lower()