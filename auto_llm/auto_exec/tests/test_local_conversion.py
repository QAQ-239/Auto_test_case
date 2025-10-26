import pytest
import json

# 定义测试固件
@pytest.fixture(scope='session')
def text_conversion_fixture():
    base_url = "http://localhost:8080/convert"
    return base_url

# 定义测试函数
def test_txt_to_md_conversion(text_conversion_fixture):
    source_text = "Hello, world!"
    expected_result = "# Hello, world!"
    result = txt_to_md(source_text)
    assert result['result'] == expected_result

def test_txt_to_json_conversion(text_conversion_fixture):
    source_text = "Hello, world!"
    expected_result = json.dumps({'text': 'Hello, world!'})
    result = txt_to_json(source_text)
    assert result['result'] == expected_result

def test_unsupported_format_conversion(text_conversion_fixture):
    source_text = "Hello, world!"
    target_format = 'pdf'
    result = txt_to_pdf(source_text)
    assert result['error'] == 'unsupported format'

# 本地文本格式转换函数定义
def txt_to_md(source_text):
    md_text = '# ' + source_text
    return {'result': md_text}

def txt_to_json(source_text):
    json_text = json.dumps({'text': source_text})
    return {'result': json_text}

def txt_to_pdf(source_text):
    return {'error': 'unsupported format'}