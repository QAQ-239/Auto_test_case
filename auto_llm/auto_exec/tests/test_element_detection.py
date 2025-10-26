import pytest
from requests.exceptions import RequestException

# 固定装置：list_data
@pytest.fixture
def list_data():
    return [1, 3, 5]

# 测试用例：Test with target in list (P0)
def test_target_in_list(list_data):
    # 步骤 1: 传入列表 [1, 3, 5] 和目标元素 3
    target = 3
    # 步骤 2: 检查函数是否返回 True
    assert target_in_list(list_data, target) == True

# 测试用例：Test with target not in list (P0)
def test_target_not_in_list(list_data):
    # 步骤 1: 传入列表 [1, 3, 5] 和目标元素 4
    target = 4
    # 步骤 2: 检查函数是否返回 False
    assert target_in_list(list_data, target) == False

# 测试用例：Test with non-list input (P0)
def test_non_list_input():
    # 步骤 1: 传入非列表输入（例如，'abc'）
    input_data = 'abc'
    # 步骤 2: 检查函数是否返回错误消息 'input is not a list'
    with pytest.raises(Exception) as excinfo:
        target_in_list(input_data, 1)
    assert str(excinfo.value) == 'input is not a list'

# 函数：target_in_list
# 功能：判断目标元素是否在列表中
def target_in_list(input_data, target):
    if not isinstance(input_data, list):
        raise Exception('input is not a list')
    return target in input_data