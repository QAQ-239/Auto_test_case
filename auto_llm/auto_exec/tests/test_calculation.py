import pytest
import requests

def test_calculation_service():
    try:
        response = requests.get("http://localhost:5000/calculation_service")
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
    except requests.exceptions.ConnectionError:
        pytest.skip("Connection refused")