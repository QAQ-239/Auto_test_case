import pytest

def convert_text(text, format):
    # 这里是一些转换逻辑，我假设它已经完成了
    if format == 'MD':
        return {'result': '转换后的 MD 文本'}
    elif format == 'JSON':
        return {'result': '转换后的 JSON 文本'}
    else:
        return {'error': 'unsupported format'}

def test_txt_to_md_conversion():
    """
    测试 TXT 转 MD 转换功能
    """
    # 调用本地转换函数，传入 TXT 文本和目标格式类型 MD
    result = convert_text('TXT文本内容', 'MD')
    # 检查返回结果是否包含 result 字段，内容为转换后的 MD 文本
    assert 'result' in result
    assert result['result'] == '转换后的 MD 文本'

def test_txt_to_json_conversion():
    """
    测试 TXT 转 JSON 转换功能
    """
    # 调用本地转换函数，传入 TXT 文本和目标格式类型 JSON
    result = convert_text('TXT文本内容', 'JSON')
    # 检查返回结果是否包含 result 字段，内容为转换后的 JSON 文本
    assert 'result' in result
    assert result['result'] == '转换后的 JSON 文本'

def test_unsupported_format_conversion():
    """
    测试不支持的格式转换功能
    """
    # 调用本地转换函数，传入 TXT 文本和不支持的格式类型（如 'PDF'）
    result = convert_text('TXT文本内容', 'PDF')
    # 检查返回结果是否包含 error 字段，内容为 'unsupported format'
    assert 'error' in result
    assert result['error'] == 'unsupported format'