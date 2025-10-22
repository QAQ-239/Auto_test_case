#!/usr/bin/env python3
"""
验证自动修复功能的基本测试
"""
import json
import tempfile
from pathlib import Path

def test_prompt_builder_repair():
    """测试 PromptBuilder 的修复功能"""
    print("=== 测试 PromptBuilder 修复功能 ===")
    
    # 添加当前目录到 Python 路径
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        from generator.prompt_builder import PromptBuilder
        
        builder = PromptBuilder()
        
        # 模拟测试套件
        suite = {
            "suite_id": "test-001",
            "suite_name": "Test Suite",
            "context": {
                "entry_point": "tests/test_example.py"
            }
        }
        
        # 模拟有问题的代码
        current_code = """def test_example():
    # 缺少 requests 导入
    response = requests.post("http://localhost:5000/api/calc", 
                           json={"operation": "add", "operands": [2, 3]})
    assert response.status_code == 200
    assert response.json()["result"] == 5"""
        
        # 模拟失败摘要
        summary = {
            "totals": {"failed": 1, "passed": 0},
            "failures": [{
                "nodeid": "test_example.py::test_example", 
                "outcome": "failed",
                "longrepr": "NameError: name 'requests' is not defined"
            }]
        }
        
        # 模拟日志
        logs = {
            "pytest_stdout": "FAILED test_example.py::test_example - NameError: name 'requests' is not defined",
            "pytest_stderr": "NameError: name 'requests' is not defined"
        }
        
        # 测试修复提示词构建
        system_prompt, user_prompt = builder.build_repair_prompts(
            suite, current_code, summary, logs
        )
        
        print("✅ 修复提示词构建成功")
        print(f"系统提示词长度: {len(system_prompt)}")
        print(f"用户提示词长度: {len(user_prompt)}")
        
        # 检查提示词内容
        assert "修复" in system_prompt
        assert "requests" in user_prompt
        assert "NameError" in user_prompt
        
        print("✅ 提示词内容验证通过")
        return True
        
    except Exception as e:
        print(f"❌ PromptBuilder 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pipeline_imports():
    """测试 pipeline 模块导入"""
    print("\n=== 测试 Pipeline 模块导入 ===")
    
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        from auto_exec.pipeline import try_auto_fix, collect_failure_context
        print("✅ pipeline 模块导入成功")
        return True
    except Exception as e:
        print(f"❌ pipeline 模块导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mock_llm_client():
    """测试 Mock LLM 客户端"""
    print("\n=== 测试 Mock LLM 客户端 ===")
    
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        from generator.llm_client import LLMClient
        
        # 创建 mock 响应文件
        mock_response = '''```python
import requests
import pytest

def test_example():
    response = requests.post("http://localhost:5000/api/calc", 
                           json={"operation": "add", "operands": [2, 3]})
    assert response.status_code == 200
    assert response.json()["result"] == 5
```'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(mock_response)
            mock_file = f.name
        
        try:
            # 创建 mock 客户端
            client = LLMClient(mode="mock", mock_response_path=mock_file)
            
            # 测试生成代码
            response = client.generate_code("系统提示词", "用户提示词")
            
            print("✅ Mock LLM 客户端测试成功")
            print(f"响应长度: {len(response)}")
            assert "import requests" in response
            print("✅ 响应内容验证通过")
            
            return True
        finally:
            Path(mock_file).unlink(missing_ok=True)
            
    except Exception as e:
        print(f"❌ Mock LLM 客户端测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始验证自动修复功能...\n")
    
    tests = [
        test_prompt_builder_repair,
        test_pipeline_imports,
        test_mock_llm_client,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"验证结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有验证通过！自动修复功能已就绪。")
        print("\n使用方法:")
        print("1. 命令行: python -m auto_exec.pipeline --suite test.json --mode mock --auto-fix")
        print("2. Gradio界面: 启用'自动修复'复选框")
    else:
        print("⚠️ 部分验证失败，请检查相关模块。")

if __name__ == "__main__":
    main()
