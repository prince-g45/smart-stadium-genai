"""
Unit tests for the Smart Fan Assistant Flask app.
Run with: pytest
"""

import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Stadium Assistant" in response.data


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_gates_endpoint_default_stadium(client):
    response = client.get("/api/gates")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)
    assert len(data) > 0


def test_gates_endpoint_specific_stadium(client):
    response = client.get("/api/gates?stadium_id=azteca")
    assert response.status_code == 200
    data = response.get_json()
    assert "Gate 1" in data


def test_gates_endpoint_unknown_stadium(client):
    response = client.get("/api/gates?stadium_id=nonexistent")
    assert response.status_code == 404


def test_stadiums_list_endpoint(client):
    response = client.get("/api/stadiums")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) >= 5
    assert "id" in data[0] and "name" in data[0] and "city" in data[0]


def test_chat_valid_message(client):
    response = client.post("/api/chat", json={"message": "Where is the washroom?"})
    assert response.status_code == 200
    data = response.get_json()
    assert "reply" in data
    assert isinstance(data["reply"], str)
    assert len(data["reply"]) > 0


def test_chat_empty_message(client):
    response = client.post("/api/chat", json={"message": ""})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_chat_missing_message_key(client):
    response = client.post("/api/chat", json={})
    assert response.status_code == 400


def test_chat_too_long_message(client):
    long_message = "a" * 501
    response = client.post("/api/chat", json={"message": long_message})
    assert response.status_code == 400


def test_chat_gate_keyword_reply(client):
    response = client.post("/api/chat", json={"message": "Where is Gate A?"})
    data = response.get_json()
    assert "gate" in data["reply"].lower()


def test_chat_medical_keyword_reply(client):
    response = client.post("/api/chat", json={"message": "I need medical help"})
    data = response.get_json()
    assert "medical" in data["reply"].lower()


def test_chat_with_stadium_id(client):
    response = client.post(
        "/api/chat",
        json={"message": "Where is the nearest gate?", "stadium_id": "sofi"},
    )
    assert response.status_code == 200
    assert "reply" in response.get_json()


def test_chat_invalid_language_falls_back(client):
    response = client.post(
        "/api/chat",
        json={"message": "Where is the food?", "language": "x" * 40},
    )
    assert response.status_code == 200


def test_reset_conversation(client):
    client.post("/api/chat", json={"message": "hello"})
    response = client.post("/api/reset")
    assert response.status_code == 200
    assert response.get_json() == {"status": "reset"}


def test_security_headers_present(client):
    response = client.get("/")
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-Content-Type-Options") == "nosniff"


def test_404_returns_json(client):
    response = client.get("/api/nonexistent-route")
    assert response.status_code == 404
    assert response.get_json()["error"] == "Not found"