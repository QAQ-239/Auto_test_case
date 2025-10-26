import pytest

# 本地函数
def is_in_range(num, min, max):
    if min > max:
        return 'Error: min cannot be greater than max'
    return min <= num <= max

# 测试用例 1：Number in Range
def test_number_in_range():
    result = is_in_range(7, 5, 10)
    assert result == True, "测试用例 1 失败：预期结果为 True，实际结果为 {}".format(result)

# 测试用例 2：Number not in Range
def test_number_not_in_range():
    result = is_in_range(3, 5, 10)
    assert result == False, "测试用例 2 失败：预期结果为 False，实际结果为 {}".format(result)

# 测试用例 3：Min Greater than Max
def test_min_greater_than_max():
    result = is_in_range(5, 10, 5)
    assert result == 'Error: min cannot be greater than max', "测试用例 3 失败：预期结果为 'Error: min cannot be greater than max'，实际结果为 {}".format(result)

if __name__ == "__main__":
    pytest.main(["-q", "tests/test_generated.py"])