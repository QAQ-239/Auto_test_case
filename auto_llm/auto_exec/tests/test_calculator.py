import pytest

def add(a, b):
    return {'result': a + b}

def sub(a, b):
    return {'result': a - b}

def mul(a, b):
    return {'result': a * b}

def div(a, b):
    if b == 0:
        return {'error': 'divide by zero'}
    return {'result': a / b}

def test_addition():
    assert add(5, 3) == {'result': 8}

def test_subtraction():
    assert sub(5, 3) == {'result': 2}

def test_multiplication():
    assert mul(5, 3) == {'result': 15}

def test_division():
    assert div(6, 3) == {'result': 2}

def test_division_by_zero():
    assert div(5, 0) == {'error': 'divide by zero'}

def test_functions_defined():
    assert add is not None
    assert sub is not None
    assert mul is not None
    assert div is not None