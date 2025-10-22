import pytest

# 定义计算器函数
def calculator_function(a, b, operation):
    if operation == 'add':
        return a + b
    elif operation == 'subtract':
        return a - b
    elif operation == 'multiply':
        return a * b
    elif operation == 'divide':
        return a / b
    else:
        raise ValueError("Invalid operation")

# 定义 fixture
@pytest.fixture
def calculator_fixture():
    return calculator_function

# 定义测试用例
def test_addition(calculator_fixture):
    # 步骤 1
    result = calculator_fixture(5, 3, 'add')
    # 步骤 2
    assert result == 8, "Expected result is 8"

def test_subtraction(calculator_fixture):
    result = calculator_fixture(5, 3, 'subtract')
    assert result == 2, "Expected result is 2"

def test_multiplication(calculator_fixture):
    result = calculator_fixture(5, 3, 'multiply')
    assert result == 15, "Expected result is 15"

def test_division(calculator_fixture):
    result = calculator_fixture(6, 3, 'divide')
    assert result == 2, "Expected result is 2"