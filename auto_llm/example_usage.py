#!/usr/bin/env python3
"""
自动修复功能使用示例
"""
import json
import tempfile
from pathlib import Path

def create_example_test_suite():
    """创建示例测试套件"""
    suite = {
        "suite_id": "example-001",
        "suite_name": "Example Test Suite",
        "description": "演示自动修复功能的示例测试套件",
        "context": {
            "target": "http://localhost:5000/api/calc",
            "language": "python",
            "framework": "pytest",
            "entry_point": "tests/test_example.py"
        },
        "fixtures": [
            {
                "name": "client",
                "type": "http",
                "details": {
                    "base_url": "http://localhost:5000/api"
                }
            }
        ],
        "test_cases": [
            {
                "id": "TC001",
                "title": "测试计算器加法",
                "priority": "P0",
                "steps": [
                    "调用 POST /calc 接口，传入 operation=add, operands=[2, 3]",
                    "校验响应状态码为 200",
                    "校验响应 JSON 中 result 字段为 5"
                ],
                "expected_result": "接口返回 result=5 且 status=200"
            }
        ]
    }
    
    suite_file = Path("example_test_suite.json")
    suite_file.write_text(json.dumps(suite, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✅ 创建示例测试套件: {suite_file}")
    return suite_file

def create_mock_response():
    """创建模拟的修复响应"""
    mock_response = '''```python
import pytest
import requests

@pytest.fixture
def client():
    """HTTP 客户端 fixture"""
    return requests.Session()

def test_tc001_calc_add(client):
    """测试计算器加法"""
    response = client.post(
        "http://localhost:5000/api/calc",
        json={"operation": "add", "operands": [2, 3]},
        timeout=5
    )
    
    # 校验响应状态码
    assert response.status_code == 200, f"期望状态码 200，实际 {response.status_code}"
    
    # 校验响应结果
    result = response.json()
    assert result["result"] == 5, f"期望结果 5，实际 {result.get('result')}"
```'''
    
    mock_file = Path("example_mock_response.md")
    mock_file.write_text(mock_response, encoding="utf-8")
    print(f"✅ 创建模拟响应文件: {mock_file}")
    return mock_file

def show_usage_examples():
    """显示使用示例"""
    print("\n" + "="*60)
    print("自动修复功能使用示例")
    print("="*60)
    
    print("\n1. 命令行使用方式:")
    print("   python -m auto_exec.pipeline \\")
    print("       --suite example_test_suite.json \\")
    print("       --mode mock \\")
    print("       --mock-response example_mock_response.md \\")
    print("       --auto-fix \\")
    print("       --max-fixes 3")
    
    print("\n2. 使用真实 LLM API:")
    print("   python -m auto_exec.pipeline \\")
    print("       --suite example_test_suite.json \\")
    print("       --mode http \\")
    print("       --http-endpoint https://api.example.com/v1/chat/completions \\")
    print("       --http-model gpt-4 \\")
    print("       --auto-fix \\")
    print("       --max-fixes 2")
    
    print("\n3. 使用本地模型:")
    print("   python -m auto_exec.pipeline \\")
    print("       --suite example_test_suite.json \\")
    print("       --mode subprocess \\")
    print("       --subprocess-cmd python scripts/qwen_cli.py --model /path/to/qwen \\")
    print("       --auto-fix \\")
    print("       --max-fixes 3")
    
    print("\n4. Gradio 界面使用:")
    print("   - 启动: python -m app")
    print("   - 在界面中启用'自动修复'复选框")
    print("   - 设置最大修复次数")
    print("   - 运行测试，系统会在失败时自动修复")
    
    print("\n5. 修复过程说明:")
    print("   - 初次执行测试失败")
    print("   - 系统收集失败日志和报告")
    print("   - 使用同一 LLM 分析错误原因")
    print("   - 生成修复后的测试代码")
    print("   - 重新执行测试验证")
    print("   - 重复直到成功或达到最大次数")

def main():
    """主函数"""
    print("自动修复功能演示")
    print("="*40)
    
    # 创建示例文件
    suite_file = create_example_test_suite()
    mock_file = create_mock_response()
    
    # 显示使用示例
    show_usage_examples()
    
    print(f"\n✅ 示例文件已创建:")
    print(f"   - 测试套件: {suite_file}")
    print(f"   - 模拟响应: {mock_file}")
    
    print(f"\n📝 下一步:")
    print(f"   1. 运行: python -m auto_exec.pipeline --suite {suite_file} --mode mock --mock-response {mock_file} --auto-fix")
    print(f"   2. 或启动 Gradio 界面: python -m app")

if __name__ == "__main__":
    main()
