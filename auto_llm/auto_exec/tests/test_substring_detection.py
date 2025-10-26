import pytest

# 测试用例 1: Substring is found
def test_substring_found():
    mainStr = 'hello world'
    subStr = 'world'
    assert subStr in mainStr, "The function should return true"

# 测试用例 2: Substring is not found
def test_substring_not_found():
    mainStr = 'hello world'
    subStr = 'test'
    assert subStr not in mainStr, "The function should return false"

# 测试用例 3: Main string is empty
def test_main_string_empty():
    mainStr = ''
    subStr = 'test'
    assert mainStr == '', "The main string cannot be empty"

# 测试用例 4: Substring is empty
def test_substring_empty():
    mainStr = 'hello world'
    subStr = ''
    assert subStr == '', "The substring cannot be empty"

# 测试用例 5: Main string and substring are both empty
def test_both_empty():
    mainStr = ''
    subStr = ''
    assert mainStr == '', "The main string cannot be empty"
    assert subStr == '', "The substring cannot be empty"

# 测试用例 6: Main string is None
def test_main_string_none():
    mainStr = None
    subStr = 'test'
    assert mainStr is None, "The main string cannot be None"

# 测试用例 7: Substring is None
def test_substring_none():
    mainStr = 'hello world'
    subStr = None
    assert subStr is None, "The substring cannot be None"

# 测试用例 8: Main string and substring are both None
def test_both_none():
    mainStr = None
    subStr = None
    assert mainStr is None, "The main string cannot be None"
    assert subStr is None, "The substring cannot be None"