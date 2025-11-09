# 导入所需的库
import unittest
import json

# 定义计算器函数
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ZeroDivisionError("divide by zero")
    return a / b

# 定义测试类
class CalculatorTest(unittest.TestCase):
    def setUp(self):
        # 设置测试固件
        self.base_url = "http://localhost:8000/calculator"

    def test_addition(self):
        # 测试加法操作
        result = add(5, 3)
        self.assertEqual(result, 8)

    def test_subtraction(self):
        # 测试减法操作
        result = subtract(5, 3)
        self.assertEqual(result, 2)

    def test_multiplication(self):
        # 测试乘法操作
        result = multiply(5, 3)
        self.assertEqual(result, 15)

    def test_division(self):
        # 测试除法操作
        result = divide(6, 3)
        self.assertEqual(result, 2)

    def test_division_by_zero(self):
        # 测试除以零的情况
        with self.assertRaises(ZeroDivisionError):
            divide(6, 0)

if __name__ == "__main__":
    unittest.main()