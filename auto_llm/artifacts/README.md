# Artifacts 目录说明

流水线执行完成后会在此目录产出测试相关文件，供下游分析与调试使用：

- `report.json`：pytest-json-report 生成的详细测试报告，包含每条用例的执行情况、步骤耗时、错误堆栈等。第四阶段模型可解析此文件定位失败原因。
- `junit.xml`：JUnit 兼容格式的结果文件，适用于 CI 平台展示测试概览或与其他系统对接。
- `coverage.xml`：pytest-cov 输出的覆盖率报告，记录代码覆盖情况，可用于可视化或质量门槛判断。
- `bench.json`：pytest-benchmark 记录的性能数据，保存基准测试的耗时统计。
- `pytest_stdout.log`：pytest 标准输出日志，包含测试执行过程中的打印信息与插件提示，便于人工追溯。
- `pytest_stderr.log`：pytest 标准错误输出，主要存放告警、错误回溯等关键信息。
- `pytest.log`：通过 `--log-file` 收集的 pytest 日志文件，按照 INFO 级别写入，包含执行阶段摘要。
- `bundle_*.zip`：collect.py 将当前目录下所有产物打包的压缩文件，命名包含 run_id，便于下游一次性下载整体结果。

注意：目录中可能保留历史执行遗留的压缩包（如 `bundle_demo-0001.zip`），若需保持最新结果，可在新执行前清理旧的 zip。
