import pytest

# 定义 HTTP 固定装置
@pytest.fixture(scope='session')
def http_fixture():
    return {
        'base_url': 'https://httpbin.org'
    }

# 定义首字母提取函数
def first_letter(string):
    if string:
        return string[0]
    else:
        raise ValueError('string cannot be empty')

# 测试用例：首字母提取正向测试 (P0)
def test_first_letter_positive(http_fixture):
    result = first_letter('apple')
    assert result == 'a', "期望结果为 'a'，实际结果为 {}".format(result)

# 测试用例：首字母提取正向测试 (P0)
def test_first_letter_positive_number(http_fixture):
    result = first_letter('1234')
    assert result == '1', "期望结果为 '1'，实际结果为 {}".format(result)

# 测试用例：首字母提取异常测试 (P0)
def test_first_letter_exception(http_fixture):
    with pytest.raises(ValueError) as e:
        first_letter('')
    assert str(e.value) == 'string cannot be empty', "期望错误消息为 'string cannot be empty'，实际错误消息为 {}".format(e.value)