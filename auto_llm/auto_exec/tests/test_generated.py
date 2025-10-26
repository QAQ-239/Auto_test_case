import pytest
import json

# 自包含的数字奇偶判断函数
def check_parity(num):
    if isinstance(num, int):
        if num % 2 == 0:
            return {'result': 'even'}
        else:
            return {'result': 'odd'}
    else:
        return {'error': 'invalid integer input'}

# 测试用例 1
def test_even_input():
    assert check_parity(8) == {'result': 'even'}

# 测试用例 2
def test_odd_input():
    assert check_parity(11) == {'result': 'odd'}

# 测试用例 3
def test_non_integer_input():
    assert check_parity(3.2) == {'error': 'invalid integer input'}

# 测试用例 4
def test_non_integer_string_input():
    assert check_parity('abc') == {'error': 'invalid integer input'}