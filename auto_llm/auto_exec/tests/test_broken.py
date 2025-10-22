import pytest
import requests

def test_broken_calc():
    response = requests.post("http://localhost:5000/api/calc", 
                           json={"operation": "add", "operands": [2, 3]})
    assert response.status_code == 200
    assert response.json()["result"] == 5