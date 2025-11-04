import pytest
import json

# 定义本地函数
def is_even(num):
    if isinstance(num, int):
        if num % 2 == 0:
            return {'result': 'even'}
        else:
            return {'result': 'odd'}
    else:
        return {'error': 'invalid integer input'}

# 定义测试用例
def test_even_input():
    result = is_even(8)
    assert result == {'result': 'even'}

def test_odd_input():
    result = is_even(11)
    assert result == {'result': 'odd'}

def test_non_integer_input():
    result = is_even(3.2)
    assert result == {'error': 'invalid integer input'}

# 运行测试
if __name__ == "__main__":
    pytest.main(["-q", "tests/test_generated.py"])