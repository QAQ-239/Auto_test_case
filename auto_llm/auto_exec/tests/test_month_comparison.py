import pytest
from datetime import datetime

def compare_months(date1, date2):
    """
    Compare two input dates
    """
    try:
        date_format = "%Y-%m"
        datetime.strptime(date1, date_format)
        datetime.strptime(date2, date_format)
    except ValueError:
        return 'invalid date format (must be YYYY-MM)'

    return date1[:7] == date2[:7]

def test_same_month():
    """
    Test if two input dates are the same month
    """
    result = compare_months('2025-10', '2025-10')
    assert result == True

def test_different_month():
    """
    Test if two input dates are not the same month
    """
    result = compare_months('2025-10', '2025-11')
    assert result == False

def test_invalid_format():
    """
    Test with invalid date format
    """
    result = compare_months('2025-13', '2025-10')
    assert result == 'invalid date format (must be YYYY-MM)'