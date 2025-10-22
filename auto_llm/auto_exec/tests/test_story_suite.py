import pytest

@pytest.fixture
def client():
    # 假设这是一个返回模拟HTTP客户端的fixture
    class MockClient:
        def post(self, url, json=None):
            if url == "/calc/add":
                return {"status_code": 200, "json": lambda: {"result": json['a'] + json['b']}}
            elif url == "/calc/sub":
                return {"status_code": 200, "json": lambda: {"result": json['a'] - json['b']}}
            elif url == "/calc/mul":
                return {"status_code": 200, "json": lambda: {"result": json['a'] * json['b']}}
            elif url == "/calc/div":
                if json['b'] == 0:
                    return {"status_code": 200, "json": lambda: {"error": "divide by zero"}}
                return {"status_code": 200, "json": lambda: {"result": json['a'] / json['b']}}
            else:
                raise ValueError(f"Unknown URL: {url}")

    return MockClient()

@pytest.mark.usefixtures("client")
def test_add(client):
    # 测试加法接口
    response = client.post("/calc/add", json={'a': 5, 'b': 3})
    assert response["status_code"] == 200
    response_json = response["json"]()
    assert "result" in response_json
    assert response_json["result"] == 8

@pytest.mark.usefixtures("client")
def test_sub(client):
    # 测试减法接口
    response = client.post("/calc/sub", json={'a': 5, 'b': 3})
    assert response["status_code"] == 200
    response_json = response["json"]()
    assert "result" in response_json
    assert response_json["result"] == 2

@pytest.mark.usefixtures("client")
def test_mul(client):
    # 测试乘法接口
    response = client.post("/calc/mul", json={'a': 5, 'b': 3})
    assert response["status_code"] == 200
    response_json = response["json"]()
    assert "result" in response_json
    assert response_json["result"] == 15

@pytest.mark.usefixtures("client")
def test_div(client):
    # 测试除法接口
    response = client.post("/calc/div", json={'a': 5, 'b': 3})
    assert response["status_code"] == 200
    response_json = response["json"]()
    assert "result" in response_json
    assert abs(response_json["result"] - 1.6666666666666667) < 1e-9

@pytest.mark.usefixtures("client")
def test_div_by_zero(client):
    # 测试除数为零的情况
    response = client.post("/calc/div", json={'a': 5, 'b': 0})
    assert response["status_code"] == 200
    response_json = response["json"]()
    assert "error" in response_json
    assert response_json["error"] == "divide by zero"