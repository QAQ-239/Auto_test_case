import pytest

# 定义子串检测函数
def detect_substring(main_str, sub_str):
    if main_str == "":
        raise ValueError("main string cannot be empty")
    return sub_str in main_str

# 创建 pytest 测试用例
def test_detect_substring():
    # 用例: Verify substring is present in main string (P0)
    assert detect_substring("hello world", "world") == True

    # 用例: Verify substring is not present in main string (P0)
    assert detect_substring("hello world", "test") == False

    # 用例: Verify error is thrown when main string is empty (P1)
    with pytest.raises(ValueError) as e:
        detect_substring("", "test")
    assert str(e.value) == "main string cannot be empty"