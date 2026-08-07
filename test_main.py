from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    # 修复为正确的健康检查路径
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_upload_missing_file():
    # 测试：如果不传文件直接请求，应该被拒绝 (返回 422 验证错误)
    response = client.post("/api/router/upload")
    assert response.status_code == 422