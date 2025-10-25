import pytest

def convert_text(text_content, target_format):
    if target_format == "MD":
        result = "# " + text_content
    elif target_format == "JSON":
        result = '{"result": "' + text_content + '"}'
    else:
        return {"error": "unsupported format"}
    return {"result": result}

def test_convert_text_to_md():
    """
    测试 TXT 转 MD 格式转换
    """
    # 准备测试数据
    text_content = "测试文本内容"
    target_format = "MD"

    # 调用本地转换函数
    result = convert_text(text_content, target_format)

    # 检查结果
    assert "result" in result, "未找到 result 字段"
    assert result["result"], "转换后的 MD 文本内容为空"


def test_convert_text_to_json():
    """
    测试 TXT 转 JSON 格式转换
    """
    # 准备测试数据
    text_content = "测试文本内容"
    target_format = "JSON"

    # 调用本地转换函数
    result = convert_text(text_content, target_format)

    # 检查结果
    assert "result" in result, "未找到 result 字段"
    assert result["result"], "转换后的 JSON 文本内容为空"


def test_convert_text_unsupported_format():
    """
    测试不支持的格式转换
    """
    # 准备测试数据
    text_content = "测试文本内容"
    target_format = "PDF"

    # 调用本地转换函数
    result = convert_text(text_content, target_format)

    # 检查结果
    assert "error" in result, "未找到 error 字段"
    assert result["error"] == "unsupported format", "错误信息不正确"