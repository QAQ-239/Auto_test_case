import requests
import pytest

@pytest.fixture
def client():
    base_url = "http://placeholder/api"
    return base_url

def test_add(client):
    """测试加法接口正常输入"""
    url = f"{client}/calc/add"
    response = requests.post(url, json={"a": 1, "b": 2})
    assert response.status_code == 200
    result = response.json()
    assert result["result"] == 3, f"Expected result to be 3, got {result['result']}"

def test_sub(client):
    """测试减法接口正常输入"""
    url = f"{client}/calc/sub"
    response = requests.post(url, json={"a": 5, "b": 3})
    assert response.status_code == 200
    result = response.json()
    assert result["result"] == 2, f"Expected result to be 2, got {result['result']}"

def test_mul(client):
    """测试乘法接口正常输入"""
    url = f"{client}/calc/mul"
    response = requests.post(url, json={"a": 4, "b": 5})
    assert response.status_code == 200
    result = response.json()
    assert result["result"] == 20, f"Expected result to be 20, got {result['result']}"

def test_div(client):
    """测试除法接口正常输入"""
    url = f"{client}/calc/div"
    response = requests.post(url, json={"a": 10, "b": 2})
    assert response.status_code == 200
    result = response.json()
    assert result["result"] == 5, f"Expected result to be 5, got {result['result']}"

def test_div_by_zero(client):
    """测试除法接口分母为0"""
    url = f"{client}/calc/div"
    response = requests.post(url, json={"a": 10, "b": 0})
    assert response.status_code == 200
    result = response.json()
    assert result["error"] == "divide by zero", f"Expected error to be 'divide by zero', got {result['error']}"

def test_add_missing_param(client):
    """测试加法接口请求体格式错误"""
    url = f"{client}/calc/add"
    response = requests.post(url, json={"a": 1})
    assert response.status_code == 400
    error = response.json()
    assert error["error"] == "缺少参数b", f"Expected error to be '缺少参数b', got {error['error']}"

def test_add_type_error(client):
    """测试加法接口请求体类型错误"""
    url = f"{client}/calc/add"
    response = requests.post(url, json={"a": "1", "b": "2"})
    assert response.status_code == 400
    error = response.json()
    assert error["error"] == "参数必须为数字类型", f"Expected error to be '参数必须为数字类型', got {error['error']}"