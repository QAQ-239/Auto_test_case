import pytest
import httpx
import time

# 引入必要的依赖
from fixtures.client import client

# 定义测试用例
def test_tc001_add(client):
    """
    测试加法接口返回正确结果
    """
    # 调用 POST /calc 接口，传入 operation=add, operands=[2, 3]
    response = client.post("/calc", json={"operation": "add", "operands": [2, 3]})
    
    # 校验响应状态码为 200
    assert response.status_code == 200
    
    # 校验响应 JSON 中 result 字段为 5
    assert response.json()["result"] == 5

def test_tc002_divide_by_zero(client):
    """
    测试除法接口处理除以零
    """
    # 调用 POST /calc 接口，传入 operation=divide, operands=[10, 0]
    response = client.post("/calc", json={"operation": "divide", "operands": [10, 0]})
    
    # 校验响应状态码为 400
    assert response.status_code == 400
    
    # 校验响应 JSON 中 error 字段包含 divide by zero
    assert "divide by zero" in response.json()["error"]

def test_tc003_multiply_performance(client, benchmark):
    """
    测试乘法接口性能基线
    """
    # 调用 POST /calc 接口，传入 operation=multiply, operands=[10, 25]
    start_time = time.time()
    response = client.post("/calc", json={"operation": "multiply", "operands": [10, 25]})
    elapsed_time = (time.time() - start_time) * 1000  # 转换为毫秒
    
    # 校验结果为 250
    assert response.json()["result"] == 250
    
    # 校验响应时间不超过 50ms
    assert elapsed_time <= 50

# 注意：此示例中的 fixtures/client.py 应该已经定义了 client fixture