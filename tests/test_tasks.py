from datetime import date, timedelta
from app.models.task import Task, PriorityEnum, StatusEnum
from app import db


def test_create_task(test_client, auth_header):
    client, app, user = test_client
    payload = {
        "title": "Test Task",
        "description": "Testing task creation",
        "priority": "HIGH",
        "status": "PENDING",
        "due_date": str(date.today() + timedelta(days=3))
    }

    res = client.post("/user/tasks/", json=payload, headers=auth_header)
    assert res.status_code == 201
    data = res.get_json()
    assert data["data"]["title"] == "Test Task"


def test_get_all_tasks(test_client, auth_header):
    client, app, user = test_client
    res = client.get("/user/tasks/", headers=auth_header)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "tasks" in data
    assert isinstance(data["tasks"], list)


def test_get_one_task(test_client, auth_header):
    client, app, user = test_client

    with app.app_context():
        task = Task(
            title="Single Task",
            description="Test fetch one",
            user_id=user.user_id
        )
        db.session.add(task)
        db.session.commit()
        tid = task.task_id

    res = client.get(f"/user/tasks/{tid}", headers=auth_header)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["title"] == "Single Task"


def test_update_task(test_client, auth_header):
    client, app, user = test_client

    with app.app_context():
        task = Task(
            title="Old Title",
            description="Old description",
            user_id=user.user_id
        )
        db.session.add(task)
        db.session.commit()
        tid = task.task_id

    res = client.put(
        f"/user/tasks/{tid}",
        json={"title": "Updated Title"},
        headers=auth_header
    )
    assert res.status_code == 200
    assert res.get_json()["data"]["title"] == "Updated Title"


def test_delete_task(test_client, auth_header):
    client, app, user = test_client

    with app.app_context():
        task = Task(title="Temp Task", user_id=user.user_id)
        db.session.add(task)
        db.session.commit()
        tid = task.task_id

    res = client.delete(f"/user/tasks/{tid}", headers=auth_header)
    assert res.status_code == 200
    assert "deleted" in res.get_json()["message"].lower()


def test_get_overdue_tasks(test_client, auth_header):
    client, app, user = test_client
    with app.app_context():
        task = Task(
            title="Old Task",
            due_date=date.today() - timedelta(days=2),
            user_id=user.user_id
        )
        db.session.add(task)
        db.session.commit()

    res = client.get("/user/tasks/overdue", headers=auth_header)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert any(t["title"] == "Old Task" for t in data)


def test_get_today_tasks(test_client, auth_header):
    client, app, user = test_client
    with app.app_context():
        task = Task(
            title="Today Task",
            due_date=date.today(),
            user_id=user.user_id
        )
        db.session.add(task)
        db.session.commit()

    res = client.get("/user/tasks/today", headers=auth_header)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert any(t["title"] == "Today Task" for t in data)


def test_get_upcoming_tasks(test_client, auth_header):
    client, app, user = test_client
    with app.app_context():
        task = Task(
            title="Future Task",
            due_date=date.today() + timedelta(days=3),
            user_id=user.user_id
        )
        db.session.add(task)
        db.session.commit()

    res = client.get("/user/tasks/upcoming", headers=auth_header)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert any(t["title"] == "Future Task" for t in data)


def test_get_task_stats(test_client, auth_header):
    client, app, user = test_client
    res = client.get("/user/tasks/stats", headers=auth_header)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "status_counts" in data
    assert "overdue_count" in data
