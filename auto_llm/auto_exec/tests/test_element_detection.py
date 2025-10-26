import pytest

# 定义一个 fixture 来获取基础 URL
@pytest.fixture
def base_url():
    return "https://httpbin.org"

# 测试用例 1：元素存在
def test_element_exists(base_url):
    list_data = [1, 3, 5]
    target = 3
    result = element_detection(base_url, list_data, target)
    assert result == True, "Expected function to return True"

# 测试用例 2：元素不存在
def test_element_does_not_exist(base_url):
    list_data = [1, 3, 5]
    target = 4
    result = element_detection(base_url, list_data, target)
    assert result == False, "Expected function to return False"

# 测试用例 3：输入不是列表
def test_input_is_not_a_list(base_url):
    target = "not a list"
    list_data = target
    with pytest.raises(TypeError) as excinfo:
        result = element_detection(base_url, list_data, target)
    assert str(excinfo.value) == 'input is not a list', "Expected function to return an error message 'input is not a list'"

# 补全 element_detection 函数
def element_detection(base_url, list_data, target):
    if not isinstance(list_data, list):
        raise TypeError('input is not a list')
    return target in list_data