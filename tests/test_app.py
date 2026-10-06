import copy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture(autouse=True)
def isolate_activities(monkeypatch):
    monkeypatch.setattr(app_module, "activities", copy.deepcopy(app_module.activities))


@pytest.fixture
def client():
    with TestClient(app_module.app, follow_redirects=False) as test_client:
        yield test_client


def test_root_redirects_to_static_app(client):
    response = client.get("/")

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json()["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_adds_participant(client):
    email = "new.student@mergington.edu"

    response = client.post("/activities/Chess%20Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert email in app_module.activities["Chess Club"]["participants"]


def test_signup_rejects_duplicate_participant(client):
    email = "michael@mergington.edu"
    participants_before = list(app_module.activities["Chess Club"]["participants"])

    response = client.post("/activities/Chess%20Club/signup", params={"email": email})

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert app_module.activities["Chess Club"]["participants"] == participants_before


def test_signup_rejects_unknown_activity(client):
    response = client.post("/activities/Unknown%20Activity/signup", params={"email": "student@example.com"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    email = "michael@mergington.edu"

    response = client.delete("/activities/Chess%20Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from Chess Club"}
    assert email not in app_module.activities["Chess Club"]["participants"]


def test_unregister_rejects_unregistered_participant(client):
    email = "not.signed.up@mergington.edu"
    participants_before = list(app_module.activities["Chess Club"]["participants"])

    response = client.delete("/activities/Chess%20Club/signup", params={"email": email})

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert app_module.activities["Chess Club"]["participants"] == participants_before


def test_unregister_rejects_unknown_activity(client):
    response = client.delete("/activities/Unknown%20Activity/signup", params={"email": "student@example.com"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"