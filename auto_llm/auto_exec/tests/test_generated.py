import pytest

def type_check(value):
    if value is None:
        return {'error': 'invalid value'}
    elif isinstance(value, (int, float)):
        return {'result': True}
    else:
        return {'result': False}

@pytest.fixture
def type_check_fixture():
    return type_check

@pytest.mark.parametrize("input, expected", [
    (123, {'result': True}),
    ("abc", {'result': False}),
    (None, {'error': 'invalid value'}),
])
def test_type_check(input, expected, type_check_fixture):
    result = type_check_fixture(input)
    assert result == expected