import pytest

# 定义测试用例的 fixture
@pytest.fixture(scope='module')
def math_operations_fixture():
    return MathOperations()

# 创建 MathOperations 类
class MathOperations:
    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b

    def multiply(self, a, b):
        return a * b

    def divide(self, a, b):
        if b == 0:
            raise ZeroDivisionError('division by zero')
        return a / b

# 加法运算测试
def test_addition(math_operations_fixture):
    result = math_operations_fixture.add(3, 5)
    assert result == 8, f"期望结果为 8，实际结果为 {result}"

# 减法运算测试
def test_subtraction(math_operations_fixture):
    result = math_operations_fixture.subtract(10, 3)
    assert result == 7, f"期望结果为 7，实际结果为 {result}"

# 乘法运算测试
def test_multiplication(math_operations_fixture):
    result = math_operations_fixture.multiply(4, 5)
    assert result == 20, f"期望结果为 20，实际结果为 {result}"

# 除法运算测试
def test_division(math_operations_fixture):
    result = math_operations_fixture.divide(10, 2)
    assert result == 5, f"期望结果为 5，实际结果为 {result}"

# 除以零的测试
def test_division_by_zero(math_operations_fixture):
    with pytest.raises(ZeroDivisionError):
        math_operations_fixture.divide(10, 0)