```python
import pytest
import requests

# 定义计算服务的 fixture
@pytest.fixture(scope="session")
def calc_fixture():
    base_url = "http://localhost:5000"
    return base_url

# 测试加法接口
def test_add_endpoint(calc_fixture):
    url = f"{calc_fixture}/calc/add"
    data = {"a": 5, "b": 3}
    response = requests.post(url, json=data)
    assert response.status_code == 200, "请求失败"
    assert "result" in response.json(), "响应中未找到 result 字段"
    assert response.json()["result"] == 8, "加法运算结果错误"

# 测试减法接口
def test_sub_endpoint(calc_fixture):
    url = f"{calc_fixture}/calc/sub"
    data = {"a": 5, "b": 3}
    response = requests.post(url, json=data)
    assert response.status_code == 200, "请求失败"
    assert "result" in response.json(), "响应中未找到 result 字段"
    assert response.json()["result"] == 2, "减法运算结果错误"

# 测试乘法接口
def test_mul_endpoint(calc_fixture):
    url = f"{calc_fixture}/calc/mul"
    data = {"a": 5, "b": 3}
    response = requests.post(url, json=data)
    assert response.status_code == 200, "请求失败"
    assert "result" in response.json(), "响应中未找到 result 字段"
    assert response.json()["result"] == 15, "乘法运算结果错误"

# 测试除法接口
def test_div_endpoint(calc_fixture):
    url = f"{calc_fixture}/calc/div"
    data = {"a": 6