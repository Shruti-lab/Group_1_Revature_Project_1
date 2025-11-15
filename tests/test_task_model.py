import pytest
from datetime import date, timedelta
from app.models import Task
from app import db


# ✅ Test 1: overdue → create valid, then manually backdate in DB
def test_is_overdue_true_via_api(test_client, auth_header):
    client, app, user = test_client

    # Create with valid (future) due_date
    payload = {
        "title": "Past Due Task",
        "due_date": str(date.today() + timedelta(days=3)),
        "priority": "LOW",
        "status": "PENDING"
    }
    res = client.post("/user/tasks/", json=payload, headers=auth_header)
    assert res.status_code == 201

    created = res.get_json()["data"]

    # Now manually backdate due_date to simulate overdue
    with app.app_context():
        task = Task.query.get(created["task_id"])
        task.due_date = date.today() - timedelta(days=2)
        db.session.commit()

    # Fetch again and check overdue flag
    res = client.get(f"/user/tasks/{created['task_id']}", headers=auth_header)
    data = res.get_json()["data"]
    assert data["is_overdue"] is True


# ✅ Test 2: completed old task → overdue should be False
def test_is_overdue_false_when_completed_via_api(test_client, auth_header):
    client, app, user = test_client

    payload = {
        "title": "Completed Old Task",
        "due_date": str(date.today() + timedelta(days=2)),
        "priority": "MEDIUM",
        "status": "COMPLETED"
    }
    res = client.post("/user/tasks/", json=payload, headers=auth_header)
    assert res.status_code == 201
    created = res.get_json()["data"]

    # Backdate for simulation
    with app.app_context():
        task = Task.query.get(created["task_id"])
        task.due_date = date.today() - timedelta(days=3)
        db.session.commit()

    res = client.get(f"/user/tasks/{created['task_id']}", headers=auth_header)
    data = res.get_json()["data"]
    assert data["is_overdue"] is False
    assert data["status"] == "COMPLETED"


# ✅ Test 3: no due_date → should not be overdue
def test_is_overdue_false_when_no_due_date_via_api(test_client, auth_header):
    client, app, user = test_client

    payload = {
        "title": "No Due Date Task",
        "priority": "HIGH",
        "status": "PENDING"
    }
    res = client.post("/user/tasks/", json=payload, headers=auth_header)
    assert res.status_code == 201
    data = res.get_json()["data"]

    assert data["is_overdue"] is False


# ✅ Test 4: to_dict serialization → check all expected fields
def test_to_dict_serialization_via_api(test_client, auth_header):
    client, app, user = test_client

    payload = {
        "title": "Serialization Task",
        "description": "Check serialized fields",
        "priority": "HIGH",
        "status": "IN_PROGRESS",
        "due_date": str(date.today() + timedelta(days=2))
    }

    res = client.post("/user/tasks/", json=payload, headers=auth_header)
    assert res.status_code == 201
    data = res.get_json()["data"]

    expected_keys = {
        "task_id", "title", "description", "start_date", "due_date",
        "priority", "status", "user_id", "is_overdue"
    }
    assert expected_keys.issubset(data.keys())


# ✅ Test 5: repr() indirectly → check returned fields reflect correct ID and status
def test_repr_format_via_api(test_client, auth_header):
    client, app, user = test_client

    payload = {
        "title": "Repr Task",
        "priority": "LOW",
        "status": "PENDING",
        "due_date": str(date.today() + timedelta(days=2))
    }

    res = client.post("/user/tasks/", json=payload, headers=auth_header)
    assert res.status_code == 201
    created = res.get_json()["data"]

    res_get = client.get(f"/user/tasks/{created['task_id']}", headers=auth_header)
    assert res_get.status_code == 200
    data = res_get.get_json()["data"]

    assert data["title"] == "Repr Task"
    assert data["status"] == "PENDING"
