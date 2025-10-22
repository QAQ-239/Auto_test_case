import pytest

class Client:
    def __init__(self, base_url):
        self.base_url = base_url

    def request(self, method, endpoint, params=None):
        # 假设这是一个简单的HTTP请求方法，实际使用requests库或其他HTTP客户端
        if method == 'GET':
            return {'method': 'GET', 'endpoint': endpoint, 'params': params}
        elif method == 'POST':
            return {'method': 'POST', 'endpoint': endpoint, 'params': params, 'Content-Type': 'application/json', 'result': 0}
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

def add(a, b):
    return a + b

def sub(a, b):
    return a - b

def mul(a, b):
    return a * b

def div(a, b):
    if b == 0:
        return {'error': 'divide by zero'}
    return a / b

@pytest.fixture
def client():
    return Client(base_url='http://placeholder/api')

def test_add(client):
    response = client.request('POST', '/add', params={'a': 5, 'b': 3})
    assert response['params'] == {'a': 5, 'b': 3}
    result = add(5, 3)
    assert result == 8

def test_sub(client):
    response = client.request('POST', '/sub', params={'a': 5, 'b': 3})
    assert response['params'] == {'a': 5, 'b': 3}
    result = sub(5, 3)
    assert result == 2

def test_mul(client):
    response = client.request('POST', '/mul', params={'a': 5, 'b': 3})
    assert response['params'] == {'a': 5, 'b': 3}
    result = mul(5, 3)
    assert result == 15

def test_div(client):
    response = client.request('POST', '/div', params={'a': 15, 'b': 3})
    assert response['params'] == {'a': 15, 'b': 3}
    result = div(15, 3)
    assert result == 5

def test_div_by_zero(client):
    response = client.request('POST', '/div', params={'a': 15, 'b': 0})
    assert response['params'] == {'a': 15, 'b': 0}
    result = div(15, 0)
    assert result == {'error': 'divide by zero'}

def test_response_format_add(client, benchmark):
    response = client.request('POST', '/add', params={'a': 5, 'b': 3})
    assert response['method'] == 'POST'
    assert response['endpoint'] == '/add'
    assert response['params'] == {'a': 5, 'b': 3}
    assert 'Content-Type' in response and response['Content-Type'] == 'application/json'
    assert 'result' in response

def test_response_format_sub(client, benchmark):
    response = client.request('POST', '/sub', params={'a': 5, 'b': 3})
    assert response['method'] == 'POST'
    assert response['endpoint'] == '/sub'
    assert response['params'] == {'a': 5, 'b': 3}
    assert 'Content-Type' in response and response['Content-Type'] == 'application/json'
    assert 'result' in response

def test_response_format_mul(client, benchmark):
    response = client.request('POST', '/mul', params={'a': 5, 'b': 3})
    assert response['method'] == 'POST'
    assert response['endpoint'] == '/mul'
    assert response['params'] == {'a': 5, 'b': 3}
    assert 'Content-Type' in response and response['Content-Type'] == 'application/json'
    assert 'result' in response

def test_response_format_div(client, benchmark):
    response = client.request('POST', '/div', params={'a': 15, 'b': 3})
    assert response['method'] == 'POST'
    assert response['endpoint'] == '/div'
    assert response['params'] == {'a': 15, 'b': 3}
    assert 'Content-Type' in response and response['Content-Type'] == 'application/json'
    assert 'result' in response