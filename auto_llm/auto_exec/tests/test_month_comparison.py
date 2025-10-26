import pytest
from datetime import datetime

# 定义测试用例
def test_compare_same_month():
    """
    测试用例：[1] Compare two identical months (P0)
    """
    assert compare_months('2025-10', '2025-10') == True

def test_compare_different_months():
    """
    测试用例：[2] Compare two different months (P0)
    """
    assert compare_months('2025-10', '2025-11') == False

def test_compare_invalid_date():
    """
    测试用例：[3] Compare a month with an invalid date (P1)
    """
    with pytest.raises(ValueError) as excinfo:
        compare_months('2025-13', '2025-10')
    assert str(excinfo.value) == 'invalid date format (must be YYYY-MM)'

# 定义比较月份的函数
def compare_months(date1, date2):
    """
    比较两个日期是否为同一个月。
    如果日期格式不正确，则抛出 ValueError。
    """
    try:
        d1 = datetime.strptime(date1, '%Y-%m')
        d2 = datetime.strptime(date2, '%Y-%m')
    except ValueError:
        raise ValueError('invalid date format (must be YYYY-MM)')
    return d1.month == d2.month and d1.year == d2.year

# 运行测试
if __name__ == '__main__':
    pytest.main(['-q', __file__])