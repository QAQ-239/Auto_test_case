# 导入所需的模块
import pytest
import json

# 定义被测函数
def compare_numbers(a, b):
    """
    这个函数比较两个数字的大小，并返回一个包含比较结果的 JSON 对象。
    如果输入不是数字，则返回一个包含错误信息的 JSON 对象。
    """
    try:
        a = float(a)
        b = float(b)
    except ValueError:
        return json.dumps({'error': 'inputs must be numbers'})

    if a > b:
        return json.dumps({'result': 'greater'})
    elif a < b:
        return json.dumps({'result': 'less'})
    else:
        return json.dumps({'result': 'equal'})

# 定义测试用例
def test_with_greater_number():
    """
    测试用例: Test with greater number (P0)
    步骤: 1. Call the function with inputs a=5 and b=3
    期望结果: {'result': 'greater'}
    """
    assert compare_numbers(5, 3) == json.dumps({'result': 'greater'})

def test_with_equal_numbers():
    """
    测试用例: Test with equal numbers (P0)
    步骤: 1. Call the function with inputs a=2 and b=2
    期望结果: {'result': 'equal'}
    """
    assert compare_numbers(2, 2) == json.dumps({'result': 'equal'})

def test_with_less_number():
    """
    测试用例: Test with less number (P0)
    步骤: 1. Call the function with inputs a=1 and b=2
    期望结果: {'result': 'less'}
    """
    assert compare_numbers(1, 2) == json.dumps({'result': 'less'})