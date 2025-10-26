import pytest
import json

# 定义用户信息
valid_user = {"account": "user123", "password": "pass456"}
invalid_user = {"account": "user456", "password": "wrong_password"}
empty_user = {"account": "", "password": ""}


# 定义本地函数来验证用户信息
def validate_user(user):
    if user['account'] == "" or user['password'] == "":
        return {"error": "account or password cannot be empty"}
    elif user['account'] == "user123" and user['password'] == "pass456":
        return {"result": True}
    else:
        return {"result": False}


# 定义测试用例
def test_valid_login():
    response = validate_user(valid_user)
    assert response['result'] == True


def test_invalid_login():
    response = validate_user(invalid_user)
    assert response['result'] == False


def test_empty_account_or_password():
    response = validate_user(empty_user)
    assert response['error'] == "account or password cannot be empty"