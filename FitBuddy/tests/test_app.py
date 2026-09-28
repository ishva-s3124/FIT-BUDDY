def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_generate_and_update(client):
    payload = {
        "user_id": "FB001",
        "name": "Alex",
        "age": 25,
        "weight": 70,
        "goal": "muscle gain",
        "intensity": "medium",
    }
    response = client.post("/api/generate-workout", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == "FB001"
    assert len(body["workout_plan"]["days"]) == 7

    feedback = client.post("/api/submit-feedback", json={"user_id": "FB001", "feedback": "Add more cardio"})
    assert feedback.status_code == 200
    assert feedback.json()["user_id"] == "FB001"


def test_home_and_admin(client):
    assert client.get("/").status_code == 200
    assert client.get("/view-all-users").status_code == 200


def test_invalid_payload_is_rejected(client):
    response = client.post("/api/generate-workout", json={
        "user_id": "X", "name": "A", "age": 10, "weight": 20,
        "goal": "invalid", "intensity": "invalid",
    })
    assert response.status_code == 422


def test_missing_feedback_user_returns_404(client):
    response = client.post("/api/submit-feedback", json={
        "user_id": "UNKNOWN", "feedback": "Add more cardio",
    })
    assert response.status_code == 404


def test_users_api(client):
    client.post("/api/generate-workout", json={
        "user_id": "FB002", "name": "Sam", "age": 30, "weight": 68,
        "goal": "general wellness", "intensity": "low",
    })
    response = client.get("/api/users")
    assert response.status_code == 200
    assert response.json()[0]["user_id"] == "FB002"
