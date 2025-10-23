# 导入必要的库
import pytest

# 定义测试用例
def test_addition():
    # 定义函数
    def add(a, b):
        return a + b

    # 执行测试
    assert add(1, 2) == 3

def test_subtraction():
    # 定义函数
    def subtract(a, b):
        return a - b

    # 执行测试
    assert subtract(5, 3) == 2

def test_multiplication():
    # 定义函数
    def multiply(a, b):
        return a * b

    # 执行测试
    assert multiply(4, 5) == 20

def test_division():
    # 定义函数
    def divide(a, b):
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return a / b

    # 执行测试
    assert divide(10, 2) == 5