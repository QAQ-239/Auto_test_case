# 导入必要的库
import pytest

# 定义测试函数
def test_addition():
    # 定义加法函数
    def add(a, b):
        return a + b

    # 执行加法操作并断言结果
    result = add(1, 2)
    assert result == 3, "加法测试失败"

def test_subtraction():
    # 定义减法函数
    def sub(a, b):
        return a - b

    # 执行减法操作并断言结果
    result = sub(5, 2)
    assert result == 3, "减法测试失败"

def test_multiplication():
    # 定义乘法函数
    def mul(a, b):
        return a * b

    # 执行乘法操作并断言结果
    result = mul(3, 2)
    assert result == 6, "乘法测试失败"

def test_division():
    # 定义除法函数
    def div(a, b):
        if b == 0:
            raise ZeroDivisionError("除数不能为零")
        return a / b

    # 执行除法操作并断言结果
    result = div(6, 2)
    assert result == 3, "除法测试失败"

# 定义主函数
if __name__ == "__main__":
    pytest.main(["-q", "tests/test_generated.py"])