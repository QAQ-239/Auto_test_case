#!/usr/bin/env python3
"""
测试自动修复功能的示例脚本
"""
import json
import subprocess
import sys
from pathlib import Path

# 创建一个有问题的测试用例（缺少导入）
def create_broken_test():
    broken_code = '''
import pytest

def test_broken_calc():
    # 缺少 requests 导入，会导致 NameError
    response = requests.post("http://localhost:5000/api/calc", 
                           json={"operation": "add", "operands": [2, 3]})
    assert response.status_code == 200
    assert response.json()["result"] == 5
'''
    
    test_file = Path("tests/test_broken.py")
    test_file.parent.mkdir(exist_ok=True)
    test_file.write_text(broken_code, encoding="utf-8")
    print(f"创建有问题的测试文件: {test_file}")

def create_test_suite():
    """创建测试套件JSON"""
    suite = {
        "suite_id": "auto-fix-test",
        "suite_name": "Auto Fix Test Suite",
        "description": "测试自动修复功能",
        "context": {
            "target": "http://localhost:5000/api/calc",
            "language": "python",
            "framework": "pytest",
            "entry_point": "tests/test_broken.py"
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
                "title": "修复导入错误",
                "priority": "P0",
                "steps": [
                    "修复缺少的 requests 导入",
                    "确保测试可以正常运行"
                ],
                "expected_result": "测试通过，无导入错误"
            }
        ]
    }
    
    suite_file = Path("test_suite_auto_fix.json")
    suite_file.write_text(json.dumps(suite, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"创建测试套件: {suite_file}")
    return suite_file

def test_auto_fix_with_mock():
    """使用 mock 模式测试自动修复"""
    print("=== 测试自动修复功能（Mock模式）===")
    
    # 创建测试文件
    create_broken_test()
    suite_file = create_test_suite()
    
    # 创建 mock 响应（修复后的代码）
    mock_response = '''
```python
import pytest
import requests

def test_broken_calc():
    response = requests.post("http://localhost:5000/api/calc", 
                           json={"operation": "add", "operands": [2, 3]})
    assert response.status_code == 200
    assert response.json()["result"] == 5
```
'''
    
    mock_file = Path("mock_repair_response.md")
    mock_file.write_text(mock_response, encoding="utf-8")
    
    # 运行 pipeline 并启用自动修复
    cmd = [
        sys.executable, "-m", "auto_exec.pipeline",
        "--suite", str(suite_file),
        "--mode", "mock",
        "--mock-response", str(mock_file),
        "--auto-fix",
        "--max-fixes", "2",
        "--dry-run"  # 只生成不执行，避免需要真实的服务
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print("STDOUT:")
    print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    print(f"退出码: {result.returncode}")
    
    # 清理
    Path("tests/test_broken.py").unlink(missing_ok=True)
    suite_file.unlink(missing_ok=True)
    mock_file.unlink(missing_ok=True)
    try:
        Path("tests").rmdir()
    except OSError:
        # 如果目录不为空，尝试删除所有文件
        import shutil
        shutil.rmtree("tests", ignore_errors=True)

if __name__ == "__main__":
    test_auto_fix_with_mock()
