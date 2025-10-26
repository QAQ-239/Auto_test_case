import pytest
import json

def first_character(s):
    if not s:
        raise ValueError('string cannot be empty')
    return s[0]

def test_first_character_normal():
    # 正常情况测试
    result = first_character('apple')
    assert result == 'a'

def test_first_character_number():
    # 数字情况测试
    result = first_character('1234')
    assert result == '1'

def test_first_character_empty():
    # 空字符串情况测试
    with pytest.raises(ValueError) as e:
        first_character('')
    assert str(e.value) == 'string cannot be empty'

if __name__ == "__main__":
    pytest.main(["-q", "tests/test_first_character.py"])