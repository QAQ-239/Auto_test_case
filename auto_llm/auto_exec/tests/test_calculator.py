import unittest

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b

class CalculatorTest(unittest.TestCase):
    def test_add(self):
        """
        测试加法操作
        """
        result = add(5, 3)
        self.assertEqual(result, 8)

    def test_subtract(self):
        """
        测试减法操作
        """
        result = subtract(5, 3)
        self.assertEqual(result, 2)

    def test_multiply(self):
        """
        测试乘法操作
        """
        result = multiply(5, 3)
        self.assertEqual(result, 15)

    def test_divide(self):
        """
        测试除法操作
        """
        result = divide(6, 3)
        self.assertEqual(result, 2)

    def test_divide_by_zero(self):
        """
        测试除以零操作
        """
        with self.assertRaises(ZeroDivisionError):
            divide(6, 0)

if __name__ == "__main__":
    unittest.main()