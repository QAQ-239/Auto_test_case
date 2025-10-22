```python
import time
from typing import Dict, List

import pytest
import requests


class CalcClient:
    """薄包装的计算器 HTTP 客户端，负责统一发起请求并记录诊断信息。"""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def operate(self, operation: str, operands: List[float]) -> requests.Response:
        payload: Dict[str, object] = {"operation": operation, "operands": operands}
        response = requests.post(f"{self.base_url}/calc", json=payload, timeout=5)
        return response


@pytest.fixture(scope="session")
def calc_client() -> CalcClient:
    return CalcClient(base_url="http://localhost:5000/api")


def assert_json_field(response: requests.Response, key: str, expected_value) -> None:
    data = response.json()
    actual = data.get(key)
    assert (
        actual == expected_value
    ), f"期望 {key}={expected_value!r}，但收到 {actual!r}；响应体={data}"


def test_tc001_add_success(calc_client: CalcClient) -> None:
    response = calc_client.operate("add", [2, 3])
    assert response.status_code == 200, f"状态码异常: {response.status_code}, body={response.text}"
    assert_json_field(response, "result", 5)


def test_tc002_divide_by_zero(calc_client: CalcClient) -> None:
    response = calc_client.operate("divide", [10, 0])
    assert response.status_code == 400, f"状态码异常: {response.status_code}, body={response.text}"
    data = response.json()
    assert "error" in data, f"响应缺少 error 字段: {data}"
    assert "divide" in data["error"].lower(), f"错误提示不包含 divide: {data['error']}"


def test_tc003_multiply_performance(calc_client: CalcClient, benchmark) -> None:
    def _operation() -> requests.Response:
        return calc_client.operate("multiply", [10, 25])

    response = benchmark(_operation)
    assert response.status_code == 200, f"状态码异常: {response.status_code}, body={response.text}"
    assert_json_field(response, "result", 250)

    stats = benchmark.stats
    avg_ms = stats["mean"] * 1000
    assert avg_ms <= 50, f"平均耗时 {avg_ms:.2f}ms 超过期望阈值 50ms"
```
