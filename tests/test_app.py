from collections.abc import Iterator
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setattr(app_module, "activities", deepcopy(app_module.activities))
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_get_activities_returns_activity_details(client: TestClient) -> None:
    response = client.get("/activities")

    assert response.status_code == 200
    activities = response.json()
    assert "Chess Club" in activities
    assert activities["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]
    assert activities["Chess Club"]["max_participants"] == 12


def test_signup_adds_participant(client: TestClient) -> None:
    activity = "Basketball Team"
    email = "new-student@mergington.edu"

    response = client.post(f"/activities/{activity}/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity}"}
    activities = client.get("/activities").json()
    assert email in activities[activity]["participants"]


def test_signup_rejects_duplicate_participant(client: TestClient) -> None:
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_rejects_unknown_activity(client: TestClient) -> None:
    response = client.post(
        "/activities/Unknown Activity/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_requires_email(client: TestClient) -> None:
    response = client.post("/activities/Chess Club/signup")

    assert response.status_code == 422


def test_unregister_removes_participant(client: TestClient) -> None:
    activity = "Chess Club"
    email = "michael@mergington.edu"

    response = client.delete(f"/activities/{activity}/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity}"}
    activities = client.get("/activities").json()
    assert email not in activities[activity]["participants"]


def test_unregister_rejects_participant_not_signed_up(client: TestClient) -> None:
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "not-signed-up@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student not signed up for this activity"


def test_unregister_rejects_unknown_activity(client: TestClient) -> None:
    response = client.delete(
        "/activities/Unknown Activity/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_requires_email(client: TestClient) -> None:
    response = client.delete("/activities/Chess Club/signup")

    assert response.status_code == 422
