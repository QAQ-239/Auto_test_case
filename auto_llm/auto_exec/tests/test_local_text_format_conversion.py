import pytest
import json

def test_txt_to_md():
    result = convert_text_format("原始文本内容", "MD")
    assert "result" in result
    assert result["result"] == "转换后的 MD 格式文本内容"

def test_txt_to_json():
    result = convert_text_format("原始文本内容", "JSON")
    assert "result" in result
    assert result["result"] == "转换后的 JSON 格式文本内容"

def test_unsupported_format():
    result = convert_text_format("原始文本内容", "PDF")
    assert "error" in result
    assert result["error"] == "unsupported format"

def convert_text_format(text, format):
    if format not in ["MD", "JSON"]:
        return {"error": "unsupported format"}
    
    if format == "MD":
        result = txt_to_md(text)
    elif format == "JSON":
        result = txt_to_json(text)
    
    return {"result": result}

def txt_to_md(text):
    # 这里实现将文本转换为 MD 格式的逻辑
    return "转换后的 MD 格式文本内容"

def txt_to_json(text):
    # 这里实现将文本转换为 JSON 格式的逻辑
    return "转换后的 JSON 格式文本内容"