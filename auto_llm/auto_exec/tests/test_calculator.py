import unittest
import json

# 创建一个模拟的 calculator_module
class MockCalculatorModule:
    @staticmethod
    def add(a, b):
        return a + b

    @staticmethod
    def sub(a, b):
        return a - b

    @staticmethod
    def mul(a, b):
        return a * b

    @staticmethod
    def div(a, b):
        if b == 0:
            raise ZeroDivisionError("division by zero")
        return a / b

# 使用模拟的 calculator_module
class CalculatorTestSuite(unittest.TestCase):
    def setUp(self):
        self.calculator = MockCalculatorModule()

    def tearDown(self):
        pass

    def test_addition(self):
        result = self.calculator.add(5, 3)
        expected = {'result': 8}
        self.assertEqual(result, expected['result'])

    def test_subtraction(self):
        result = self.calculator.sub(5, 3)
        expected = {'result': 2}
        self.assertEqual(result, expected['result'])

    def test_multiplication(self):
        result = self.calculator.mul(5, 3)
        expected = {'result': 15}
        self.assertEqual(result, expected['result'])

    def test_division(self):
        result = self.calculator.div(9, 3)
        expected = {'result': 3}
        self.assertEqual(result, expected['result'])

    def test_division_by_zero(self):
        with self.assertRaises(ZeroDivisionError) as context:
            self.calculator.div(9, 0)
        self.assertTrue('division by zero' in str(context.exception))

if __name__ == "__main__":
    unittest.main()