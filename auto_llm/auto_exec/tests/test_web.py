import pytest

@pytest.fixture
def client():
    from requests import Session

    session = Session()
    session.base_url = "http://placeholder/api"
    return session

def test_add_normal(client):
    """
    测试加法接口正常输入
    """
    response = client.post("/calc/add", json={"a": 5, "b": 3})
    assert response.status_code == 200
    result = response.json()
    assert result["result"] == 8, "加法结果不正确"

def test_sub_normal(client):
    """
    测试减法接口正常输入
    """
    response = client.post("/calc/sub", json={"a": 5, "b": 3})
    assert response.status_code == 200
    result = response.json()
    assert result["result"] == 2, "减法结果不正确"

def test_mul_normal(client):
    """
    测试乘法接口正常输入
    """
    response = client.post("/calc/mul", json={"a": 5, "b": 3})
    assert response.status_code == 200
    result = response.json()
    assert result["result"] == 15, "乘法结果不正确"

def test_div_normal(client):
    """
    测试除法接口正常输入
    """
    response = client.post("/calc/div", json={"a": 10, "b": 2})
    assert response.status_code == 200
    result = response.json()
    assert result["result"] == 5, "除法结果不正确"

def test_div_zero(client):
    """
    测试除法接口除数为零
    """
    response = client.post("/calc/div", json={"a": 10, "b": 0})
    assert response.status_code == 200
    result = response.json()
    assert result["error"] == "divide by zero", "除数为零时未返回正确的错误信息"