import pytest
import json

# 定义计算函数
def add(a, b):
    return {'result': a + b}

def sub(a, b):
    return {'result': a - b}

def mul(a, b):
    return {'result': a * b}

def div(a, b):
    if b == 0:
        return {'error': 'divide by zero'}
    return {'result': a / b}

# 定义测试用例
def test_addition():
    result = add(5, 3)
    assert 'result' in result
    assert result['result'] == 8

def test_subtraction():
    result = sub(5, 3)
    assert 'result' in result
    assert result['result'] == 2

def test_multiplication():
    result = mul(5, 3)
    assert 'result' in result
    assert result['result'] == 15

def test_division():
    result = div(6, 3)
    assert 'result' in result
    assert result['result'] == 2

    result = div(6, 0)
    assert 'error' in result
    assert result['error'] == 'divide by zero'

if __name__ == "__main__":
    pytest.main(['-q', 'test_generated.py'])