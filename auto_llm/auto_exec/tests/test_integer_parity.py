import pytest
import requests
import json

# 测试套件 ID: 1
# 测试套件名称: 数字奇偶判断
# 套件描述: 判断输入的单个整数是奇数还是偶数
# 目标语言: python
# 测试框架: pytest
# 入口文件: tests/test_integer_parity.py
# 目标系统/地址: https://httpbin.org
# 可用的固定装置（fixtures）：
# - 名称: integer_fixture
#   类型: http
#   详细配置:
#     base_url: https://httpbin.org

base_url = "https://httpbin.org"

def is_even(num):
    """判断一个数字是否为偶数"""
    return num % 2 == 0

def is_integer(num):
    """判断一个字符串是否为整数"""
    try:
        int(num)
        return True
    except ValueError:
        return False

def integer_parity(num):
    """判断一个数字是奇数还是偶数"""
    if not is_integer(num):
        return {'error': 'invalid integer input'}
    if is_even(num):
        return {'result': 'even'}
    else:
        return {'result': 'odd'}

def test_odd_number():
    """奇数测试"""
    num = 11
    assert integer_parity(num) == {'result': 'odd'}

def test_even_number():
    """偶数测试"""
    num = 8
    assert integer_parity(num) == {'result': 'even'}

def test_non_integer_input():
    """非整数输入测试"""
    num = 'abc'
    assert integer_parity(num) == {'error': 'invalid integer input'}

# 运行测试
if __name__ == "__main__":
    pytest.main([__file__])