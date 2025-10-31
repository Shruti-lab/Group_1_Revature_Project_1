import click
import requests
import json
import os
from datetime import datetime

API_URL = "http://127.0.0.1:5000"     
TOKEN_FILE = "token.txt"               

# ---- USER COMMANDS ----

def save_token(token):
    with open(TOKEN_FILE, "w") as f:
        f.write(token)

def load_token():
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE, "r") as f:
        return f.read().strip()

@click.group()
def cli():
    """TaskFlow CLI Tool"""
    pass

# SIGNUP COMMAND
@cli.command()
@click.option("--name", required=True, help="User Full Name")
@click.option("--email", required=True, help="User Email")
@click.option("--password", required=True, help="User Password")
def signup(name, email, password):
    """Register a new user"""
    payload = {"name": name, "email": email, "password": password}
    res = requests.post(f"{API_URL}/auth/signup", json=payload)

    click.echo(res.json())

# LOGIN COMMAND
@cli.command()
@click.option("--email", required=True, help="User Email")
@click.option("--password", required=True, help="User Password")
def login(email, password):
    """Login and save JWT token"""
    payload = {"email": email, "password": password}
    res = requests.post(f"{API_URL}/auth/login", json=payload)

    data = res.json()

    if res.status_code == 200 and "access_token" in data:
        save_token(data["access_token"])
        click.echo("Login successful. Token saved.")
    else:
        click.echo(data)

# GET CURRENT USER
@cli.command()
def user():
    """Get logged-in user profile"""
    token = load_token()
    if not token:
        return click.echo(" You must login first")

    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(f"{API_URL}/auth/user", headers=headers)

    click.echo(res.json())

#  UPDATE USER PROFILE
@cli.command()
@click.option("--name", required=False, help="New Name")
@click.option("--password", required=False, help="New Password")
def update_user(name, password):
    """Update logged-in user profile"""
    token = load_token()
    if not token:
        return click.echo(" You must login first")

    payload = {}
    if name: payload["name"] = name
    if password: payload["password"] = password

    headers = {"Authorization": f"Bearer {token}"}
    res = requests.put(f"{API_URL}/auth/user", json=payload, headers=headers)

    click.echo(res.json())

# ---- TASK COMMANDS ----

from datetime import date

#  CREATE TASK
@cli.command()
@click.option("--title", prompt="Title", help="Task title")
@click.option("--description", prompt="Description", help="Task description")
@click.option("--status", default="PENDING", help="Task status (PENDING, IN_PROGRESS, COMPLETED, CANCELLED)")
@click.option("--priority", default="LOW", help="Task priority (LOW, MEDIUM, HIGH)")
@click.option("--due_date", help="Due date (YYYY-MM-DD)")
@click.option("--start_date", help="Start date (YYYY-MM-DD)")
def create(title, description, status, priority, due_date, start_date):
    """Create a new task"""
    token = load_token()
    if not token:
        click.echo("Login required.")
        return

    url = f"{API_URL}/user/tasks/"
    headers = {"Authorization": f"Bearer {token}"}

    body = {
        "title": title,
        "description": description,
        "status": status.upper(),
        "priority": priority.upper(),
        "start_date": start_date or str(date.today()),
        "due_date": due_date
    }

    response = requests.post(url, json=body, headers=headers)
    try:
        click.echo(json.dumps(response.json(), indent=2))
    except:
        click.echo(response.text)



# GET ALL TASKS
@cli.command()
def list():
    pass


#  LIST TASKS COMMAND
@cli.command()
@click.option("--status", type=str, help="Filter by status (PENDING, IN_PROGRESS, COMPLETED, CANCELLED)")
@click.option("--priority", type=str, help="Filter by priority (LOW, MEDIUM, HIGH)")
@click.option("--search", type=str, help="Search keyword in task title/description")
@click.option("--page", default=1, type=int, help="Page number")
@click.option("--per_page", default=5, type=int, help="Tasks per page")
def list(status, priority, search, page, per_page):
    """List all tasks with optional filters"""
    token = load_token()
    if not token:
        click.echo(" Error: You must login first")
        return

    url = f"{API_URL}/user/tasks"

    params = {
        "status": status,
        "priority": priority,
        "search": search,
        "page": page,
        "per_page": per_page
    }

    headers = {"Authorization": f"Bearer {token}"}

    try:
        res = requests.get(url, params=params, headers=headers)

        if res.status_code != 200:
            click.echo(f" Failed: {res.json().get('message')}")
            return

        data = res.json().get("data", {})
        tasks = data.get("tasks", [])
        pagination = data.get("pagination", {})

        click.echo("\nTask List:")
        if not tasks:
            click.echo("No tasks found.")
            return

        for t in tasks:
            click.echo(f" - {t['task_id']} | {t['title']} | {t['status']} | {t['priority']} | Due: {t['due_date']}")

        click.echo("\nPagination Info:")
        click.echo(json.dumps(pagination, indent=4))

    except Exception as e:
        click.echo(f" Error: {str(e)}")

# GET ONE TASK
@cli.command()
@click.argument("task_id", type=int)
def get_task(task_id):
    """Get details of a specific task by ID"""
    token_path = "token.txt"

    # Check if user is logged in
    if not os.path.exists(token_path):
        click.echo("Please login first using the login command.")
        return

    with open(token_path, "r") as f:
        token = f.read().strip()

    headers = {"Authorization": f"Bearer {token}"}

    API_URL = f"http://127.0.0.1:5000/user/tasks/{task_id}"
    res = requests.get(API_URL, headers=headers)

    if res.status_code == 200:
        data = res.json()
        click.echo(json.dumps(data, indent=2))
    elif res.status_code == 404:
        click.echo("Task not found.")
    else:
        click.echo(f"Error: {res.status_code}")
        click.echo(res.json())



# UPDATE TASK
@cli.command()
@click.argument("task_id", type=int)
@click.option("--title", help="New title")
@click.option("--description", help="New description")
@click.option("--status", help="New status (PENDING, IN_PROGRESS, COMPLETED, CANCELLED)")
@click.option("--priority", help="New priority (LOW, MEDIUM, HIGH)")
@click.option("--due_date", help="New due date (YYYY-MM-DD)")
def update(task_id, title, description, status, priority, due_date):
    """Update an existing task by ID"""
    token = load_token()
    if not token:
        click.echo("Login required.")
        return

    url = f"{API_URL}/user/tasks/{task_id}"
    headers = {"Authorization": f"Bearer {token}"}

    body = {}
    if title:
        body["title"] = title
    if description:
        body["description"] = description
    if status:
        body["status"] = status.upper()
    if priority:
        body["priority"] = priority.upper()
    if due_date:
        body["due_date"] = due_date

    if not body:
        click.echo("Nothing to update.")
        return

    response = requests.put(url, json=body, headers=headers)
    try:
        click.echo(json.dumps(response.json(), indent=2))
    except:
        click.echo(response.text)


#  DELETE TASK
@cli.command()
@click.argument("task_id", type=int)
def delete(task_id):
    """Delete a task by ID"""
    token = load_token()
    if not token:
        click.echo(" Login required.")
        return

    url = f"{API_URL}/user/tasks/{task_id}"
    headers = {"Authorization": f"Bearer {token}"}

    confirm = click.confirm(f"Are you sure you want to delete task {task_id}?", default=False)
    if not confirm:
        click.echo("Cancelled.")
        return

    response = requests.delete(url, headers=headers)
    try:
        click.echo(json.dumps(response.json(), indent=2))
    except:
        click.echo(response.text)
    
if __name__ == "__main__":
    cli()