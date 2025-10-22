import pytest
import requests

BASE_URL = "http://placeholder/api"

def test_addition():
    response = requests.get(f"{BASE_URL}/addition", params={"a": 1, "b": 2})
    assert response.status_code == 200
    assert response.json()["result"] == 3

def test_subtraction():
    response = requests.get(f"{BASE_URL}/subtraction", params={"a": 5, "b": 3})
    assert response.status_code == 200
    assert response.json()["result"] == 2

def test_multiplication():
    response = requests.get(f"{BASE_URL}/multiplication", params={"a": 4, "b": 5})
    assert response.status_code == 200
    assert response.json()["result"] == 20

def test_division():
    response = requests.get(f"{BASE_URL}/division", params={"a": 10, "b": 2})
    assert response.status_code == 200
    assert response.json()["result"] == 5

def test_integer_division():
    response = requests.get(f"{BASE_URL}/integer_division", params={"a": 10, "b": 3})
    assert response.status_code == 200
    assert response.json()["result"] == 3

def test_float_division():
    response = requests.get(f"{BASE_URL}/float_division", params={"a": 10, "b": 3})
    assert response.status_code == 200
    assert response.json()["result"] == 3.33

# Continue with the rest of the tests...