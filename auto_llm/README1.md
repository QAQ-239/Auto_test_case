## 自动化执行框架使用说明

### 目录结构
```
auto_exec/
  case_inputs/
    test_suite_math.json   # 标准化测试用例样例（计算器场景）
    test_suite_auth.json   # 标准化测试用例样例（认证场景）
  generator/
    main.py                # 第二阶段脚本生成入口
    prompt_builder.py      # 提示词构建
    llm_client.py          # LLM 调用封装
    tooling.py             # 工具方法（提取代码块、写文件）
  pipeline.py              # 一键生成+执行流水线入口
  scripts/
    qwen_cli.py            # HuggingFace 本地模型包装脚本
  mock_responses/
    calc_basic.md          # 本地调试用的模型响应样例
  runner/
    run.py        # 主执行器
    collect.py    # 指标汇总与打包
  tests/
    test_rand_demo.py
  artifacts/      # 执行产物输出目录
  input_examples/
    exec_request.json
  requirements.txt
```

### 快速开始：执行链路
1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
2. 执行样例请求：
   ```bash
   python runner/run.py input_examples/exec_request.json
   ```
3. 完成后可在 `artifacts/` 中查看生成的 `report.json`、`junit.xml`、`coverage.xml`、`bench.json`、压缩包等产物。
   - 额外输出：`pytest_stdout.log`、`pytest_stderr.log`、`pytest.log`，以及汇总失败详情的 `summary` JSON（运行器标准输出），便于下游模型分析。

### 快速开始：脚本生成（第二阶段）
1. 准备标准化测试用例（可参考 `case_inputs/` 目录）。
2. 通过 mock 响应验证流程（从仓库根目录执行）：
   ```bash
   python -m auto_llm.generator.main --suite auto_llm/case_inputs/test_suite_math.json \
       --mode mock --mock-response auto_llm/mock_responses/calc_basic.md
   ```
   执行后将在 `tests/` 下生成 `test_calc_api.py`。
3. 若需要连接 HuggingFace 下载的本地模型（例如 Qwen2.5），先确保 `auto_exec/scripts/qwen_cli.py` 可访问模型目录，再执行：
   ```bash
   python -m auto_llm.generator.main --suite auto_llm/case_inputs/test_suite_math.json \
       --subprocess-cmd "python auto_llm/scripts/qwen_cli.py --model /home/Newdisk2/aofanyu/qwen2.5"
   ```
   包装脚本会负责加载模型并通过 stdin/stdout 与生成器通信。
   运行此脚本需要安装 `transformers`、`torch` 等依赖，可根据本地硬件选择合适版本。
4. 若需通过 HTTP API 调用（类 OpenAI 接口），示例：
   ```bash
   export LLM_API_KEY="sk-xxxx"
   python -m auto_llm.generator.main --suite auto_llm/case_inputs/test_suite_math.json \
       --mode http --http-endpoint https://api.example.com/v1/chat/completions \
       --http-model qwen-max --http-header "X-Project:demo"
   ```
   默认会从 `LLM_API_KEY` 环境变量读取 token，并自动携带 `Authorization: Bearer ...` 头，可通过 `--http-api-key` 或 `--http-api-key-env` 自定义。

### 开发思路
- run.py 基于执行请求构造 pytest 命令，支持重试、超时、并行（需安装 pytest-xdist）等配置，并在执行完成后触发 collect.py。
- collect.py 汇总 pytest json 报告生成结构化摘要，同时打包 artifacts 产物用于后续分析。
- generator/main.py 封装了“提示词构建 → 调用模型 → 写入脚本”的流程，可通过 mock 或本地模型验证闭环。
- 测试用例使用随机示例验证通过、失败、跳过、性能与异常场景，便于下游大模型分析；`case_inputs/` 则提供更贴近业务的标准化用例样例。

### 一键流水线
使用 `pipeline.py` 完成“生成脚本 → 执行测试 → 收集产物”全流程：
```bash
python -m auto_llm.auto_exec.pipeline \
    --suite auto_llm/case_inputs/test_suite_math.json \
    --subprocess-cmd "python auto_llm/scripts/qwen_cli.py --model /home/Newdisk2/aofanyu/qwen2.5"
```
- 参数与 `generator/main.py` 保持一致，可换成 `--mode mock --mock-response ...` 等。
- 如执行器位于其他目录，可额外加上 `--runner-path /绝对路径/runner/run.py`。
- 脚本会基于 `input_examples/exec_request.json` 构造临时执行请求，只运行新生成的脚本。
- 执行结果、stdout/stderr、pytest 日志与压缩包仍输出在 `artifacts/`，供后续大模型分析。
- 若需走 HTTP API，可替换为：
  ```bash
  export LLM_API_KEY="sk-xxxx"
  python -m auto_llm.auto_exec.pipeline \
      --suite auto_llm/case_inputs/test_suite_math.json \
      --mode http --http-endpoint https://api.example.com/v1/chat/completions \
      --http-model qwen-max --http-header "X-Project:demo" \
      --request-template auto_llm/input_examples/exec_request.json \
      --runner-path /home/Newdisk2/aofanyu/project/autotask/auto_llm/runner/run.py
  ```

### 可视化 Demo（Gradio）
1. 安装依赖（包含 `gradio`、`requests` 等）：
   ```bash
   pip install -r auto_llm/requirements.txt
   ```
2. 启动网页版：
   ```bash
   PYTHONPATH=/home/Newdisk2/aofanyu/project/autotask python -m auto_llm.app
   ```
   页面中可粘贴或编辑标准用例 JSON，选择 LLM 模式（mock/本地/HTTP），点击“运行流水线”即可查看生成脚本、执行摘要、stdout/stderr 以及打包产物下载链接。
