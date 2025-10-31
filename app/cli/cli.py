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
    
# BULK DELETE TASKS

@cli.command("bulk-delete")
@click.option("--ids", multiple=True, required=True, type=int, help="Task IDs to delete (e.g. --ids 1 2 3)")
def bulk_delete(ids):
    """Delete multiple tasks by IDs"""
    token = load_token()
    if not token:
        click.echo("Login required.")
        return

    # Convert multiple IDs to comma-separated string
    ids_str = ",".join(map(str, ids))
    url = f"{API_URL}/user/tasks/bulk_delete?task_ids={ids_str}"
    headers = {"Authorization": f"Bearer {token}"}

    # Confirm before deleting
    confirm = click.confirm(f"Are you sure you want to delete tasks {ids_str}?", default=False)
    if not confirm:
        click.echo("Cancelled.")
        return

    response = requests.delete(url, headers=headers)

    try:
        click.echo(json.dumps(response.json(), indent=2))
    except Exception:
        click.echo(response.text)

if __name__ == "__main__":
    cli()