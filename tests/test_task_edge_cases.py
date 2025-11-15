import pytest
from datetime import date, timedelta
from sqlalchemy.exc import IntegrityError
from app.models import Task
from app import db


# ----------------- MODEL VALIDATION TESTS -----------------
def test_task_without_title_fails(test_client):
    client, app, user = test_client
    with app.app_context():
        t = Task(user_id=user.user_id, priority="HIGH", status="PENDING")
        db.session.add(t)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()


def test_task_without_user_fails(test_client):
    client, app, user = test_client
    with app.app_context():
        t = Task(title="Orphan Task", priority="LOW", status="PENDING")
        db.session.add(t)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

def test_create_task_with_invalid_priority(test_client, auth_header):
    client, app, user = test_client
    payload = {
        "title": "Bad Priority",
        "priority": "INVALID",
        "status": "PENDING"
    }

    res = client.post("/user/tasks/", json=payload, headers=auth_header)
    assert res.status_code == 400

    # Decode response bytes to string
    res_text = res.data.decode()
    # Check that the word "priority" appears in the error text
    assert "priority" in res_text

def test_create_task_with_invalid_status(test_client, auth_header):
    client, app, user = test_client
    payload = {
        "title": "Bad Status",
        "priority": "LOW",
        "status": "UNKNOWN"
    }

    res = client.post("/user/tasks/", json=payload, headers=auth_header)
    assert res.status_code == 400

    # Decode response bytes to string
    res_text = res.data.decode()
    # Check that the word "status" appears in the error text
    assert "status" in res_text

# ----------------- API BEHAVIOR TESTS -----------------

def test_update_nonexistent_task(test_client, auth_header):
    client, app, user = test_client
    res = client.put("/user/tasks/99999", json={"title": "Updated"}, headers=auth_header)
    assert res.status_code == 404


def test_delete_nonexistent_task(test_client, auth_header):
    client, app, user = test_client
    res = client.delete("/user/tasks/99999", headers=auth_header)
    assert res.status_code == 404


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


def test_get_task_unauthorized(test_client):
    client, app, user = test_client
    res = client.get("/user/tasks/")
    assert res.status_code == 401


def test_create_task_unauthorized(test_client):
    client, app, user = test_client
    payload = {"title": "No Auth Task", "priority": "LOW", "status": "PENDING"}
    res = client.post("/user/tasks/", json=payload)
    assert res.status_code == 401


def test_upcoming_tasks_excludes_today(test_client, auth_header):
    client, app, user = test_client

    # create one for today and one for tomorrow
    today_payload = {
        "title": "Today Task",
        "due_date": str(date.today()),
        "priority": "MEDIUM",
        "status": "PENDING"
    }
    tomorrow_payload = {
        "title": "Tomorrow Task",
        "due_date": str(date.today() + timedelta(days=1)),
        "priority": "HIGH",
        "status": "PENDING"
    }

    client.post("/user/tasks/", json=today_payload, headers=auth_header)
    client.post("/user/tasks/", json=tomorrow_payload, headers=auth_header)

    res = client.get("/user/tasks/upcoming", headers=auth_header)
    data = res.get_json()["data"]

    titles = [t["title"] for t in data]
    assert "Tomorrow Task" in titles
    assert "Today Task" not in titles


def test_user_cannot_access_another_users_task(test_client, auth_header, another_user_token):
    client, app, user = test_client

    # Create with user1
    payload = {
        "title": "Private Task",
        "priority": "LOW",
        "status": "PENDING"
    }
    res = client.post("/user/tasks/", json=payload, headers=auth_header)
    task_id = res.get_json()["data"]["task_id"]

    # Try to access with another user's token
    res = client.get(f"/user/tasks/{task_id}", headers=another_user_token)
    assert res.status_code in (403, 404)


def test_tasks_filtered_by_user(test_client, auth_header, another_user_token):
    client, app, user = test_client

    # User1 task
    client.post("/user/tasks/", json={"title": "U1 Task", "priority": "LOW", "status": "PENDING"}, headers=auth_header)
    # User2 task
    client.post("/user/tasks/", json={"title": "U2 Task", "priority": "LOW", "status": "PENDING"}, headers=another_user_token)

    res1 = client.get("/user/tasks/", headers=auth_header)
    res2 = client.get("/user/tasks/", headers=another_user_token)

    data1 = res1.get_json().get("data", {})
    data2 = res2.get_json().get("data", {})

    tasks_user1 = data1.get("tasks", [])
    tasks_user2 = data2.get("tasks", [])

    titles_user1 = [t["title"] for t in tasks_user1]
    titles_user2 = [t["title"] for t in tasks_user2]

    assert "U1 Task" in titles_user1
    assert "U2 Task" not in titles_user1
    assert "U2 Task" in titles_user2
    assert "U1 Task" not in titles_user2


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
        # Images can be None or list
        # assert task["images"] is None or isinstance(task["images"], list)
