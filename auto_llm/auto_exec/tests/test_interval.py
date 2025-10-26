import pytest

def interval(num, min, max):
    if min > max:
        raise ValueError('min cannot be greater than max')
    return min <= num <= max

class TestInterval:
    def setup_class(self):
        self.fixture = "http_fixture"  # 使用固定装置

    def test_case_1(self):
        # 用例: [1] 数字在区间内 (P0)
        result = interval(7, 5, 10)
        assert result == True, "期望结果为 True，但得到 False"

    def test_case_2(self):
        # 用例: [2] 数字不在区间内 (P0)
        result = interval(3, 5, 10)
        assert result == False, "期望结果为 False，但得到 True"

    def test_case_3(self):
        # 用例: [3] 最小值大于最大值 (P1)
        with pytest.raises(ValueError) as e:
            interval(5, 10, 5)
        assert str(e.value) == 'min cannot be greater than max', "期望结果为 'min cannot be greater than max'，但得到不同的错误"

if __name__ == "__main__":
    pytest.main(["-q", "tests/test_interval.py"])