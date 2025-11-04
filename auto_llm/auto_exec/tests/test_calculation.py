# 导入所需的库
import unittest
import json

# 计算模块
def add(a, b):
    return {'result': a + b}

def subtract(a, b):
    return {'result': a - b}

def multiply(a, b):
    return {'result': a * b}

def divide(a, b):
    if b == 0:
        return {'error': 'divide by zero'}
    else:
        return {'result': a / b}

# 测试类
class TestCalculation(unittest.TestCase):

    def test_add(self):
        # 测试加法
        result = add(5, 3)
        expected_result = {'result': 8}
        self.assertEqual(result, expected_result)

    def test_subtract(self):
        # 测试减法
        result = subtract(5, 3)
        expected_result = {'result': 2}
        self.assertEqual(result, expected_result)

    def test_multiply(self):
        # 测试乘法
        result = multiply(5, 3)
        expected_result = {'result': 15}
        self.assertEqual(result, expected_result)

    def test_divide(self):
        # 测试除法
        result = divide(6, 3)
        expected_result = {'result': 2}
        self.assertEqual(result, expected_result)

    def test_divide_by_zero(self):
        # 测试除以零
        result = divide(5, 0)
        expected_result = {'error': 'divide by zero'}
        self.assertEqual(result, expected_result)

if __name__ == '__main__':
    unittest.main()