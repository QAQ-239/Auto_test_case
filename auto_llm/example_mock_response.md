```python
import pytest
import requests

@pytest.fixture
def client():
    """HTTP 客户端 fixture"""
    return requests.Session()

def test_tc001_calc_add(client):
    """测试计算器加法"""
    response = client.post(
        "http://localhost:5000/api/calc",
        json={"operation": "add", "operands": [2, 3]},
        timeout=5
    )
    
    # 校验响应状态码
    assert response.status_code == 200, f"期望状态码 200，实际 {response.status_code}"
    
    # 校验响应结果
    result = response.json()
    assert result["result"] == 5, f"期望结果 5，实际 {result.get('result')}"
```