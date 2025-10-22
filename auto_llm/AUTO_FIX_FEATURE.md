# 自动修复功能说明

## 功能概述

在原有的"生成脚本 → 执行测试 → 收集产物"流程基础上，新增了**自动修复**功能。当测试执行失败时，系统会使用同一大模型分析失败日志，自动修复测试代码，并重新执行验证。

## 核心特性

### 1. 智能错误分析
- 自动收集 pytest 报告、JUnit XML、覆盖率报告、执行日志等
- 基于失败摘要和详细日志进行错误原因分析
- 保持与生成脚本使用相同的 LLM 客户端，确保一致性

### 2. 迭代修复机制
- 支持多次修复尝试（默认最多2次）
- 每次修复后重新执行测试验证
- 修复成功则停止，达到最大次数则停止

### 3. 修复策略
- 修复导入缺失（如 requests、httpx、pytest 等）
- 调整 HTTP 客户端配置（base_url、超时、headers）
- 修正断言逻辑（状态码、响应字段、错误信息匹配）
- 添加异常处理和重试机制
- 修正 fixture 定义和作用域
- 处理异步/同步调用不匹配问题

## 使用方法

### 命令行方式

```bash
# 启用自动修复
python -m auto_llm.auto_exec.pipeline \
    --suite test_suite.json \
    --mode http --http-endpoint https://api.example.com/v1/chat/completions \
    --auto-fix --max-fixes 3 \
    --artifacts-path /path/to/artifacts
```

### Gradio 界面方式

1. 在界面中启用"自动修复"复选框
2. 设置最大修复尝试次数（1-5次）
3. 指定测试产物目录路径
4. 运行流水线，系统会在失败时自动尝试修复

## 新增参数

- `--auto-fix`：启用自动修复功能
- `--max-fixes`：最大修复尝试次数（默认2次）
- `--artifacts-path`：测试产物目录路径（包含日志和报告）

## 技术实现

### 1. 提示词构建（PromptBuilder）
- 新增 `build_repair_prompts()` 方法
- 构建专门的修复提示词，包含失败摘要和日志信息
- 支持自定义修复策略模板

### 2. 流水线集成（pipeline.py）
- 新增 `try_auto_fix()` 函数实现迭代修复逻辑
- 新增 `collect_failure_context()` 函数收集失败上下文
- 在 `main()` 函数中集成自动修复流程

### 3. 界面支持（app.py）
- 新增自动修复相关的 UI 控件
- 修改 `run_pipeline_interactive()` 函数支持自动修复参数
- 在测试失败时自动触发修复流程

## 文件结构

```
auto_llm/
├── generator/
│   └── prompt_builder.py          # 新增修复提示词构建
├── auto_exec/
│   └── pipeline.py                # 新增自动修复逻辑
├── app.py                         # 新增UI控件和流程集成
├── repair_template_example.md     # 修复提示词模板示例
├── test_auto_fix.py              # 自动修复功能测试脚本
└── AUTO_FIX_FEATURE.md           # 本说明文档
```

## 使用示例

### 场景1：导入错误修复
```python
# 原始代码（有问题）
def test_api():
    response = requests.post(...)  # 缺少 requests 导入

# 修复后代码
import requests
def test_api():
    response = requests.post(...)
```

### 场景2：HTTP客户端配置修复
```python
# 原始代码（有问题）
def test_api():
    response = requests.post("http://localhost:5000/api/calc", ...)

# 修复后代码
@pytest.fixture
def client():
    return requests.Session()

def test_api(client):
    response = client.post("/calc", ...)  # 使用相对路径和fixture
```

## 注意事项

1. **LLM一致性**：修复过程使用与生成脚本相同的LLM客户端
2. **迭代限制**：建议设置合理的最大修复次数（2-3次），避免无限循环
3. **日志分析**：系统会分析多种日志格式，提供全面的失败上下文
4. **修复质量**：基于工程最佳实践进行修复，避免掩盖真实问题
5. **资源消耗**：每次修复都会重新调用LLM和执行测试，注意API调用成本

## 扩展性

- 支持自定义修复提示词模板
- 可扩展支持更多编程语言和测试框架
- 支持更复杂的修复策略（如依赖管理、环境配置等）
- 可集成到CI/CD流程中实现自动化测试修复
