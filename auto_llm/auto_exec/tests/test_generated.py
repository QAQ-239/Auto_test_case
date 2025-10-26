# 导入所需的模块
import pytest
import json

# 定义测试套件 ID 和名称
suite_id = "1"
suite_name = "Numeric Comparison Suite"

# 定义测试用例
test_cases = [
    {"name": "Test Greater (P0)", "input": {"a": 5, "b": 3}, "expected": {"result": "greater"}},
    {"name": "Test Less (P0)", "input": {"a": 2, "b": 5}, "expected": {"result": "less"}},
    {"name": "Test Equal (P0)", "input": {"a": 2, "b": 2}, "expected": {"result": "equal"}},
    {"name": "Test Non-numeric input (P0)", "input": {"a": 'abc', "b": 2}, "expected": {"error": "inputs must be numbers"}},
]

# 定义 compare_numbers 函数
def compare_numbers(a, b):
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        return {"error": "inputs must be numbers"}
    elif a > b:
        return {"result": "greater"}
    elif a < b:
        return {"result": "less"}
    else:
        return {"result": "equal"}

# 定义测试函数
@pytest.mark.parametrize("test_case", test_cases)
def test_numeric_comparison(test_case):
    # 调用函数
    result = compare_numbers(test_case["input"]["a"], test_case["input"]["b"])
    
    # 检查结果
    if "error" in test_case["expected"]:
        assert result["error"] == test_case["expected"]["error"]
    else:
        assert result == test_case["expected"]