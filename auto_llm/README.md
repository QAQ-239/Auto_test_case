## 自动化测试生成与执行平台说明

### 目录结构
```
auto_llm/
  case_inputs/              # 标准化测试用例样例
  generator/                # 第二阶段脚本生成模块
  auto_exec/                # 流水线与运行器
  mock_responses/           # mock 模式样例响应
  runner/                   # pytest 执行与汇总脚本
  scripts/                  # 本地模型包装脚本
  artifacts/                # 测试产物输出目录
  input_examples/           # 执行模板
  requirements.txt
```

### 快速开始：执行链路
1. 安装依赖：
   ```bash
   pip install -r auto_llm/requirements.txt
   ```
2. 执行样例请求：
   ```bash
   python auto_llm/runner/run.py auto_llm/input_examples/exec_request.json
   ```
3. 测试产物位于 `auto_llm/artifacts/`，包含 `report.json`、`junit.xml`、`coverage.xml`、`bench.json`、`pytest_stdout.log`、`pytest_stderr.log`、`pytest.log` 以及打包好的 `bundle_*.zip`，便于后续模型与人工分析。

### 测试用例生成（第一阶段）
- 支持通过自然语言用户故事生成标准化测试套件，并直接衔接脚本生成与执行：
  ```bash
  export LLM_API_KEY="sk-xxxx"
  python -m auto_llm.auto_exec.pipeline \
      --story-file story.txt \
      --mode http --http-endpoint https://api.example.com/v1/chat/completions \
      --http-model qwen-max --http-header "X-Project:demo" \
      --suite-id blog-api-smoke-001 --suite-name "Blog API 冒烟测试" \
      --target http://localhost:8000 --entry-point tests/test_blog_api.py \
      --request-template auto_llm/input_examples/exec_request.json \
      --runner-path /home/Newdisk2/aofanyu/project/autotask/auto_llm/runner/run.py
  ```
  - 若未指定 `--suite`，生成的 JSON 会写入临时文件并继续流程；也可使用 `--suite output_suite.json` 落盘。
  - `--suite-id` / `--suite-name` / `--target` / `--entry-point` / `--fixtures-hint` 为可选提示，可帮助大模型补齐上下文信息。
  - 同时提供 `--story` 与 `--suite` 时，优先使用用户故事生成的内容。

### 脚本生成（第二阶段）
- 使用 mock 响应验证流程：
  ```bash
  python -m auto_llm.generator.main --suite auto_llm/case_inputs/test_suite_math.json \
      --mode mock --mock-response auto_llm/mock_responses/calc_basic.md
  ```
- 接入本地模型（subprocess 模式）：
  ```bash
  python -m auto_llm.generator.main --suite auto_llm/case_inputs/test_suite_math.json \
      --subprocess-cmd "python auto_llm/scripts/qwen_cli.py --model /home/Newdisk2/aofanyu/qwen2.5"
  ```
- 使用 HTTP API（OpenAI 兼容）：
  ```bash
  export LLM_API_KEY="sk-xxxx"
  python -m auto_llm.generator.main --suite auto_llm/case_inputs/test_suite_math.json \
      --mode http --http-endpoint https://api.example.com/v1/chat/completions \
      --http-model qwen-max --http-header "X-Project:demo"
  ```

### 一键流水线（脚本生成 + 执行）
```bash
python -m auto_llm.auto_exec.pipeline \
    --suite auto_llm/case_inputs/test_suite_math.json \
    --subprocess-cmd "python auto_llm/scripts/qwen_cli.py --model /home/Newdisk2/aofanyu/qwen2.5"
```
- 参数与 `generator/main.py` 保持一致，可切换 mock、subprocess、http 模式。
- 若执行器不在默认位置，可加入 `--runner-path /绝对路径/runner/run.py`。
- 输出的结构化摘要中包含日志、报告、打包产物路径，位于 `auto_llm/artifacts/`。
- 若需要直接从用户故事开始，可与第一阶段参数组合使用。

### 自动修复功能
```bash
python -m auto_llm.auto_exec.pipeline \
    --suite auto_llm/case_inputs/test_suite_math.json \
    --mode http --http-endpoint https://api.example.com/v1/chat/completions \
    --auto-fix --max-fixes 3 \
    --artifacts-path /home/Newdisk2/aofanyu/project/autotask/auto_llm/artifacts
```
- `--auto-fix`：启用失败后自动分析与修复流程。
- `--max-fixes`：最大修复次数（默认 2）。
- `--artifacts-path`：指定日志/报告目录，用于 LLM 分析。
- 修复成功后会自动回放测试并更新脚本。

### 可视化 Demo（Gradio）
1. 启动：
   ```bash
   PYTHONPATH=/home/Newdisk2/aofanyu/project/autotask python -m auto_llm.app
   ```
2. 页面提供“用户故事/需求文档”和“标准化测试用例 JSON”两个输入区，可任选其一；右侧面板提供模型模式、HTTP/本地配置以及自动修复开关。
3. 点击“运行流水线”后，可按顺序查看：生成的测试套件 JSON、测试脚本、执行摘要、stdout/stderr、产物路径与压缩包下载。

### 核心模块
- `testcase_generator.py`：用户故事 → 标准化测试用例。
- `generator/main.py`：标准化测试用例 → pytest 脚本。
- `auto_exec/pipeline.py`：整合生成、执行、自动修复，支持 HTTP/mock/本地模型。
- `runner/run.py`、`runner/collect.py`：实际执行与结果汇总。

该平台实现了“用户故事 → 测试用例 → 测试脚本 → 自动执行 → 自动修复”的完整闭环，所有产物与日志统一保存在 `auto_llm/artifacts/`，便于第四阶段大模型进一步分析与纠偏。
python -m auto_llm.auto_exec.pipeline --story-file /home/Newdisk2/aofanyu/project/autotask/auto_llm/simple_story.txt --mode subprocess --subprocess-cmd "python /home/Newdisk2/aofanyu/project/autotask/auto_llm/scripts/qwen_cli.py --model /home/Newdisk2/aofanyu/qwen2.5" --suite-id story-suite-001 --suite-name "Story Derived Test Suite" --target http://localhost:8000 --entry-point tests/test_story_suite.py --request-template /home/Newdisk2/aofanyu/project/autotask/auto_llm/input_examples/exec_request.json --runner-path /home/Newdisk2/aofanyu/project/autotask/auto_llm/runner/run.py --auto-fix --max-fixes 2 --artifacts-path /home/Newdisk2/aofanyu/project/autotask/auto_llm/artifacts