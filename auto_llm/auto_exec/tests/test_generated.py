import pytest
import json

# 本地函数，用于检查输入值是否为数字
def is_number(value):
    if value is None:
        return False
    elif isinstance(value, (int, float)):
        return True
    else:
        return False

# 测试用例：正向测试 - 输入为数字 (P0)
def test_positive_case():
    value = 123
    result = True
    assert is_number(value) == result

# 测试用例：异常处理 - 输入为 null (P0)
def test_null_case():
    value = None
    result = False
    assert is_number(value) == result

# 测试用例：异常处理 - 输入为 undefined (P0)
def test_undefined_case():
    value = 'undefined'
    result = False
    assert is_number(value) == result