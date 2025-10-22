import pytest

# 定义固定装置
@pytest.fixture
def calc_fixture():
    class Calculator:
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
    return Calculator()

# 测试用例 1：加法测试
def test_addition(calc_fixture):
    result = calc_fixture.add(1, 2)
    assert result == 3, "加法测试失败"

# 测试用例 2：减法测试
def test_subtraction(calc_fixture):
    result = calc_fixture.subtract(5, 3)
    assert result == 2, "减法测试失败"

# 测试用例 3：乘法测试
def test_multiplication(calc_fixture):
    result = calc_fixture.multiply(4, 5)
    assert result == 20, "乘法测试失败"

# 测试用例 4：除法测试
def test_division(calc_fixture):
    result = calc_fixture.divide(10, 2)
    assert result == 5, "除法测试失败"

# 测试用例 5：除以零测试
def test_division_by_zero(calc_fixture):
    with pytest.raises(ZeroDivisionError) as e:
        calc_fixture.divide(1, 0)
    assert str(e.value) == 'division by zero', "除以零测试失败"