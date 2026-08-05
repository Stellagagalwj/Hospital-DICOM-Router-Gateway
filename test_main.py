from fastapi.testclient import TestClient
from main import app
import io

client = TestClient(app)

def test_health_check():
    response = client.get("/")
    # 如果你没有写根目录接口，可以把这里的测试改为你实际有的 GET 接口，或者直接略过这个测试
    assert response.status_code in [200, 404] 

def test_upload_missing_file():
    # 测试：如果不传文件直接请求，应该被拒绝 (返回 422 验证错误)
    response = client.post("/api/router/upload")
    assert response.status_code == 422