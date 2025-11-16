from datetime import date, timedelta, datetime
from flask_jwt_extended import create_access_token
from app.models.task import Task, PriorityEnum, StatusEnum
from app.models.user import User
from app import db


# ------------------------------------------------------
# CREATE TASK — EDGE CASES
# ------------------------------------------------------

def test_create_task_missing_title(test_client, auth_header):
    client, app, user = test_client

    payload = {
        "description": "Missing title field",
        "priority": "LOW"
    }

    res = client.post(
        "/user/tasks/",
        data=payload,
        headers=auth_header,
        content_type="multipart/form-data"
    )

    assert res.status_code == 400


def test_create_task_invalid_date_format(test_client, auth_header):
    client, app, user = test_client

    payload = {
        "title": "Bad Date",
        "due_date": "not-a-valid-date"
    }

    res = client.post(
        "/user/tasks/",
        data=payload,
        headers=auth_header,
        content_type="multipart/form-data"
    )

    assert res.status_code == 400


def test_create_task_invalid_priority(test_client, auth_header):
    client, app, user = test_client

    payload = {
        "title": "Bad Priority",
        "priority": "INVALID_OPTION"
    }

    res = client.post(
        "/user/tasks/",
        data=payload,
        headers=auth_header,
        content_type="multipart/form-data"
    )

    assert res.status_code == 400


# ------------------------------------------------------
# GET TASK — EDGE CASES
# ------------------------------------------------------

def test_get_task_not_found(test_client, auth_header):
    client, app, user = test_client

    res = client.get("/user/tasks/99999", headers=auth_header)

    assert res.status_code == 404


def test_get_task_of_other_user_forbidden(test_client, auth_header):
    client, app, user = test_client

    with app.app_context():
        other = User(name="Other", email="other@example.com")
        other.set_password("password123")
        db.session.add(other)
        db.session.commit()

        task = Task(title="Other Task", user_id=other.user_id)
        db.session.add(task)
        db.session.commit()

        # Store ID BEFORE context ends
        tid = task.task_id

    # Now safe to use outside the context
    res = client.get(f"/user/tasks/{tid}", headers=auth_header)

    assert res.status_code == 404



# ------------------------------------------------------
# UPDATE TASK — EDGE CASES
# ------------------------------------------------------

def test_update_task_not_found(test_client, auth_header):
    client, app, user = test_client

    res = client.put(
        "/user/tasks/55555",
        data={"title": "Nothing"},
        headers=auth_header,
        content_type='multipart/form-data'
    )

    assert res.status_code == 404


def test_update_task_invalid_status_enum(test_client, auth_header):
    client, app, user = test_client

    with app.app_context():
        task = Task(title="Status Test", user_id=user.user_id)
        db.session.add(task)
        db.session.commit()
        tid = task.task_id

    res = client.put(
        f"/user/tasks/{tid}",
        data={"status": "WRONG_STATUS"},
        headers=auth_header,
        content_type="multipart/form-data"
    )

    assert res.status_code == 400



# ------------------------------------------------------
# DELETE TASK — EDGE CASES
# ------------------------------------------------------

def test_delete_task_not_found(test_client, auth_header):
    client, app, user = test_client

    res = client.delete("/user/tasks/99999", headers=auth_header)
    assert res.status_code == 404


def test_delete_task_twice(test_client, auth_header):
    client, app, user = test_client

    with app.app_context():
        task = Task(title="Delete Twice", user_id=user.user_id)
        db.session.add(task)
        db.session.commit()
        tid = task.task_id

    # First delete
    res1 = client.delete(f"/user/tasks/{tid}", headers=auth_header)
    assert res1.status_code == 200

    # Second delete → should not find
    res2 = client.delete(f"/user/tasks/{tid}", headers=auth_header)
    assert res2.status_code == 404


# ------------------------------------------------------
# TODAY / UPCOMING / OVERDUE — EDGE CASES
# ------------------------------------------------------

def test_today_tasks_empty(test_client, auth_header):
    client, app, user = test_client

    res = client.get("/user/tasks/today", headers=auth_header)
    assert res.status_code == 200
    assert res.get_json()["data"] == []


def test_upcoming_tasks_none(test_client, auth_header):
    client, app, user = test_client

    res = client.get("/user/tasks/upcoming", headers=auth_header)
    assert res.status_code == 200
    assert res.get_json()["data"] == []


def test_overdue_tasks_none(test_client, auth_header):
    client, app, user = test_client

    res = client.get("/user/tasks/overdue", headers=auth_header)
    assert res.status_code == 200
    assert res.get_json()["data"] == []


# ------------------------------------------------------
# STATS — EDGE CASES
# ------------------------------------------------------

def test_task_stats_no_tasks(test_client, auth_header):
    client, app, user = test_client

    res = client.get("/user/tasks/stats", headers=auth_header)
    assert res.status_code == 200

    data = res.get_json()["data"]
    assert data["status_counts"]["completed"] == 0
    assert data["status_counts"]["pending"] == 0
    assert data["overdue_count"] == 0


# ------------------------------------------------------
# AUTH / TOKEN EDGE CASES
# ------------------------------------------------------

def test_tasks_api_invalid_token(test_client):
    client, app, user = test_client

    bad_header = {"Authorization": "Bearer INVALIDTOKEN123"}

    res = client.get("/user/tasks/", headers=bad_header)

    assert res.status_code == 401




def test_create_task_with_invalid_date_format(test_client, auth_header):
    client, app, user = test_client
    payload = {
        "title": "Bad Date Task",
        "due_date": "32-13-2024",  # invalid format
        "priority": "LOW",
        "status": "PENDING"
    }
    res = client.post("/user/tasks/", json=payload, headers=auth_header)
    assert res.status_code == 400




def test_create_task_unauthorized(test_client):
    client, app, user = test_client
    payload = {"title": "No Auth Task", "priority": "LOW", "status": "PENDING"}
    res = client.post("/user/tasks/", json=payload)
    assert res.status_code == 401

def test_get_tasks_pagination(test_client, auth_header):
    """
    GIVEN a valid JWT and multiple tasks in the database
    WHEN GET /user/tasks/?page=2&per_page=5 is called
    THEN it should return only 5 tasks on page 2 and correct pagination metadata
    """
    client, app, user = test_client

    with app.app_context():
        from app.models import Task, StatusEnum, PriorityEnum, db

        # --- Setup: create 15 test tasks for this user ---
        tasks = [
            Task(
                title=f"Task {i}",
                description=f"Description {i}",
                status=StatusEnum.PENDING,
                priority=PriorityEnum.LOW,
                user_id=user.user_id,
            )
            for i in range(1, 16)
        ]
        db.session.add_all(tasks)
        db.session.commit()

    # --- Act ---
    res = client.get("/user/tasks/?page=2&per_page=5", headers=auth_header)
    data = res.get_json()

    # --- Assert ---
    assert res.status_code == 200
    assert data["message"] == "Tasks fetched successfully"
    assert data["success"] is True

    # --- Pagination Data ---
    page_data = data["data"]
    assert page_data["page"] == 2
    assert page_data["total_pages"] == 3  # 15 tasks / 5 per page
    assert page_data["total_tasks"] == 15

    # --- Tasks ---
    tasks_list = page_data["tasks"]
    assert len(tasks_list) == 5

    for task in tasks_list:
        assert "task_id" in task
        assert "title" in task
        assert "status" in task
        assert "priority" in task
        assert "is_overdue" in task
        assert isinstance(task["is_overdue"], bool)
    
