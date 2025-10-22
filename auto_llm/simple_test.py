#!/usr/bin/env python3
"""
简单的功能测试脚本
"""
import sys
from pathlib import Path

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """测试模块导入"""
    print("=== 测试模块导入 ===")
    
    try:
        from auto_exec.pipeline import parse_args, build_client, try_auto_fix
        print("✅ auto_exec.pipeline 导入成功")
    except ImportError as e:
        print(f"❌ auto_exec.pipeline 导入失败: {e}")
        return False
    
    try:
        from generator.prompt_builder import PromptBuilder
        print("✅ generator.prompt_builder 导入成功")
    except ImportError as e:
        print(f"❌ generator.prompt_builder 导入失败: {e}")
        return False
    
    try:
        from generator.llm_client import LLMClient
        print("✅ generator.llm_client 导入成功")
    except ImportError as e:
        print(f"❌ generator.llm_client 导入失败: {e}")
        return False
    
    return True

def test_prompt_builder():
    """测试 PromptBuilder 的修复功能"""
    print("\n=== 测试 PromptBuilder 修复功能 ===")
    
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
        
        # 模拟当前代码
        current_code = "def test_example():\n    assert True"
        
        # 模拟失败摘要
        summary = {
            "totals": {"failed": 1, "passed": 0},
            "failures": [{"nodeid": "test_example.py::test_example", "outcome": "failed"}]
        }
        
        # 模拟日志
        logs = {
            "pytest_stdout": "FAILED test_example.py::test_example - AssertionError",
            "pytest_stderr": "AssertionError: assert False"
        }
        
        # 测试修复提示词构建
        system_prompt, user_prompt = builder.build_repair_prompts(
            suite, current_code, summary, logs
        )
        
        print("✅ 修复提示词构建成功")
        print(f"系统提示词长度: {len(system_prompt)}")
        print(f"用户提示词长度: {len(user_prompt)}")
        
        return True
        
    except Exception as e:
        print(f"❌ PromptBuilder 测试失败: {e}")
        return False

def test_pipeline_args():
    """测试 pipeline 参数解析"""
    print("\n=== 测试 Pipeline 参数解析 ===")
    
    try:
        from auto_exec.pipeline import parse_args
        import argparse
        
        # 模拟命令行参数
        test_args = [
            "--suite", "test.json",
            "--mode", "mock",
            "--mock-response", "mock.md",
            "--auto-fix",
            "--max-fixes", "3",
            "--artifacts-path", "/tmp/artifacts"
        ]
        
        # 临时修改 sys.argv
        original_argv = sys.argv
        sys.argv = ["pipeline.py"] + test_args
        
        try:
            args = parse_args()
            print("✅ 参数解析成功")
            print(f"  auto_fix: {args.auto_fix}")
            print(f"  max_fixes: {args.max_fixes}")
            print(f"  artifacts_path: {args.artifacts_path}")
            return True
        finally:
            sys.argv = original_argv
            
    except Exception as e:
        print(f"❌ Pipeline 参数解析失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始功能测试...\n")
    
    tests = [
        test_imports,
        test_prompt_builder,
        test_pipeline_args,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！自动修复功能已就绪。")
    else:
        print("⚠️ 部分测试失败，请检查相关模块。")

if __name__ == "__main__":
    main()
