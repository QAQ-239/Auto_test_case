import requests
import pytest

@pytest.fixture
def client():
    base_url = "http://placeholder/api"
    return lambda endpoint, data: requests.post(f"{base_url}{endpoint}", json=data)

def test_add(client):
    """[001] 加法接口正常输入 (P0)"""
    response = client("/calc/add", {"a": 5, "b": 3})
    assert response.status_code == 200
    assert response.json()["result"] == 8

def test_sub(client):
    """[002] 减法接口正常输入 (P0)"""
    response = client("/calc/sub", {"a": 7, "b": 2})
    assert response.status_code == 200
    assert response.json()["result"] == 5

def test_mul(client):
    """[003] 乘法接口正常输入 (P0)"""
    response = client("/calc/mul", {"a": 4, "b": 6})
    assert response.status_code == 200
    assert response.json()["result"] == 24

def test_div(client):
    """[004] 除法接口正常输入 (P0)"""
    response = client("/calc/div", {"a": 9, "b": 3})
    assert response.status_code == 200
    assert response.json()["result"] == 3

def test_div_by_zero(client):
    """[005] 除法接口分母为0 (P0)"""
    response = client("/calc/div", {"a": 10, "b": 0})
    assert response.status_code == 200
    assert response.json()["error"] == "divide by zero"

def test_add_json_response(client):
    """[006] 加法接口响应为JSON且包含result字段 (P0)"""
    response = client("/calc/add", {"a": 1, "b": 1})
    assert response.status_code == 200
    assert "result" in response.json()

def test_sub_json_response(client):
    """[007] 减法接口响应为JSON且包含result字段 (P0)"""
    response = client("/calc/sub", {"a": 2, "b": 1})
    assert response.status_code == 200
    assert "result" in response.json()

def test_mul_json_response(client):
    """[008] 乘法接口响应为JSON且包含result字段 (P0)"""
    response = client("/calc/mul", {"a": 2, "b": 2})
    assert response.status_code == 200
    assert "result" in response.json()

def test_div_json_response(client):
    """[009] 除法接口响应为JSON且包含error字段 (P0)"""
    response = client("/calc/div", {"a": 1, "b": 0})
    assert response.status_code == 200
    assert "error" in response.json()