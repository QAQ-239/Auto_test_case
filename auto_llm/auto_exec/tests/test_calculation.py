import unittest
import json

class CalculationModuleTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_addition(self):
        # 调用加法函数
        result = add(10, 5)
        # 检查结果
        self.assertEqual(result, 15)

    def test_subtraction(self):
        # 调用减法函数
        result = subtract(10, 5)
        # 检查结果
        self.assertEqual(result, 5)

    def test_multiplication(self):
        # 调用乘法函数
        result = multiply(10, 5)
        # 检查结果
        self.assertEqual(result, 50)

    def test_division(self):
        # 调用除法函数
        result = json.loads(divide(10, 5))
        # 检查结果
        self.assertEqual(result['result'], 2)

    def test_division_by_zero(self):
        # 调用除法函数
        error = json.loads(divide(10, 0))['error']
        # 检查错误信息
        self.assertEqual(error, 'divide by zero')

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        return json.dumps({'error': 'divide by zero'})
    else:
        return json.dumps({'result': a / b})

if __name__ == '__main__':
    unittest.main()