import unittest
from calculation_module import add, subtract, multiply, divide

class TestCalculation(unittest.TestCase):
    def setUp(self):
        pass

    def test_addition(self):
        result = add(5, 3)
        self.assertEqual(result, 8)

    def test_subtraction(self):
        result = subtract(5, 3)
        self.assertEqual(result, 2)

    def test_multiplication(self):
        result = multiply(5, 3)
        self.assertEqual(result, 15)

    def test_division(self):
        result = divide(6, 3)
        self.assertEqual(result, 2)

    def test_divide_by_zero(self):
        with self.assertRaises(ZeroDivisionError):
            divide(5, 0)

if __name__ == '__main__':
    unittest.main()