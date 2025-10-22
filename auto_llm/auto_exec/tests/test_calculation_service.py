
import pytest
import requests

# 定义客户端 fixture
@pytest.fixture(scope='module')
def client():
    base_url = 'http://localhost:8000/api'
    return requests.Session().mount(base_url, requests.adapters.HTTPAdapter(max_retries=3))

# 测试用例 [1] 测试加法接口
def test_addition_api(client):
    url = 'http://localhost:8000/api/calc/add'
    data = {'a': 5, 'b': 3}
    response = client.post(url, json=data)

    # 检查响应状态码
    assert response.status_code == 200, f"期望状态码为 200，实际状态码为 {response.status_code}"

    # 检查响应内容
    assert 'result' in response.json(), f"响应中不包含 'result' 字段"
    assert response.json()['result'] == 8, f"期望结果为 8，实际结果为 {response.json()['result']}"

# 测试用例 [2] 测试减法接口
def test_subtraction_api(client):
    url = 'http://localhost:8000/api/calc/sub'
    data = {'a': 5, 'b': 3}
    response = client.post(url, json=data)

    # 检查响应状态码
    assert response.status_code == 200, f"期望状态码为 200，实际状态码为 {response.status_code}"

    # 检查响应内容
    assert 'result' in response.json(), f"响应中不包含 'result' 字段"
    assert response.json()['result'] == 2, f"期望结果为 2，实际结果为 {response.json()['result']}"

# 测试用例 [3] 测试乘法接口
def test_multiplication_api(client):
    url = 'http://localhost:8000/api/cal'