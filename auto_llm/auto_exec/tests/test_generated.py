# 导入所需的库
import pytest
from datetime import datetime

# 定义本地函数
def is_same_month(date1, date2):
    """
    比较两个日期是否为同一个月
    """
    try:
        date1 = datetime.strptime(date1, "%Y-%m")
        date2 = datetime.strptime(date2, "%Y-%m")
    except ValueError:
        return {"error": "invalid date format (must be YYYY-MM)"}

    return date1.month == date2.month and date1.year == date2.year

# 定义测试用例
def test_same_dates():
    """
    测试两个相同的日期
    """
    result = is_same_month("2025-10", "2025-10")
    assert result == True

def test_different_dates():
    """
    测试两个不同的日期
    """
    result = is_same_month("2025-10", "2025-11")
    assert result == False

def test_invalid_date_format():
    """
    测试无效的日期格式
    """
    result = is_same_month("2025-13", "2025-11")
    assert result == {"error": "invalid date format (must be YYYY-MM)"}