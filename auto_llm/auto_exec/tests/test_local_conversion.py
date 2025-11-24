import pytest
import json

# 创建一个模拟的 convert_text_format 函数
def convert_text_format(original_text, target_format):
    if target_format == 'MD':
        return {'result': f'## {original_text}'}
    elif target_format == 'JSON':
        return {'result': json.dumps({'text': original_text})}
    else:
        return {'error': 'unsupported format'}

# 定义测试用例
def test_convert_text_format_to_md():
    """
    测试 TXT 转 MD 的功能
    """
    # 准备测试数据
    original_text = "Hello, world!"
    target_format = 'MD'

    # 调用转换函数
    result = convert_text_format(original_text, target_format)

    # 检查结果
    assert 'result' in result
    assert result['result'] == f'## {original_text}'

def test_convert_text_format_to_json():
    """
    测试 TXT 转 JSON 的功能
    """
    # 准备测试数据
    original_text = "Hello, world!"
    target_format = 'JSON'

    # 调用转换函数
    result = convert_text_format(original_text, target_format)

    # 检查结果
    assert 'result' in result
    assert json.loads(result['result']) == {'text': original_text}

def test_convert_text_format_unsupported_format():
    """
    测试不支持的格式转换
    """
    # 准备测试数据
    original_text = "Hello, world!"
    target_format = 'PDF'

    # 调用转换函数
    result = convert_text_format(original_text, target_format)

    # 检查结果
    assert 'error' in result
    assert result['error'] == 'unsupported format'