import pytest
import json

# 自包含的用户验证函数
def validate_user(account, password):
    # 预设账号密码
    correct_account = "user123"
    correct_password = "pass456"

    # 检查账号密码是否为空
    if account == "" or password == "":
        return json.dumps({"error": "account or password cannot be empty"})
    # 检查账号密码是否正确
    elif account == correct_account and password == correct_password:
        return json.dumps({"result": True})
    else:
        return json.dumps({"result": False})

# 测试用例 1：有效登录
def test_valid_login():
    # 调用登录端点
    response = validate_user("user123", "pass456")
    # 检查响应
    assert json.loads(response)["result"] == True

# 测试用例 2：无效登录
def test_invalid_login():
    # 调用登录端点
    response = validate_user("user456", "pass456")
    # 检查响应
    assert json.loads(response)["result"] == False

# 测试用例 3：账号或密码为空
def test_empty_credentials():
    # 调用登录端点
    response = validate_user("", "pass456")
    # 检查响应
    assert json.loads(response)["error"] == "account or password cannot be empty"

# 入口文件
if __name__ == "__main__":
    pytest.main(["-q", "test_login.py"])