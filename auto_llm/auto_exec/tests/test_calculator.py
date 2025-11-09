import pytest

# 定义测试用例
test_cases = [
    ('add', 3, 5, {'result': 8}),
    ('subtract', 10, 4, {'result': 6}),
    ('multiply', 2, 9, {'result': 18}),
    ('divide', 15, 3, {'result': 5}),
]

# 创建一个函数来模拟 calculator 模块的行为
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ZeroDivisionError("division by zero")
    else:
        return a / b

@pytest.mark.parametrize("func_name, a, b, expected", test_cases)
def test_calculator_operations(func_name, a, b, expected):
    """
    测试计算器的加法、减法、乘法和除法操作。
    """
    func = globals()[func_name]
    if func_name == 'divide' and b == 0:
        with pytest.raises(ZeroDivisionError) as e:
            func(a, b)
        assert str(e.value) == "division by zero"
    else:
        result = func(a, b)
        assert result == expected['result']