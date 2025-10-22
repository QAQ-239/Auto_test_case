import unittest

class CalculationModuleTestSuite(unittest.TestCase):

    def test_addition_operation(self):
        # 步骤1: 调用add函数
        result = add(5, 3)
        # 步骤2: 检查结果
        self.assertEqual(result, 8)

    def test_subtraction_operation(self):
        # 步骤1: 调用subtract函数
        result = subtract(5, 3)
        # 步骤2: 检查结果
        self.assertEqual(result, 2)

    def test_multiplication_operation(self):
        # 步骤1: 调用multiply函数
        result = multiply(5, 3)
        # 步骤2: 检查结果
        self.assertEqual(result, 15)

    def test_division_operation(self):
        # 步骤1: 调用divide函数
        result = divide(6, 3)
        # 步骤2: 检查结果
        self.assertEqual(result, 2)

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    return a / b

if __name__ == '__main__':
    unittest.main()