import click
import requests
import json
import os

API_URL = "http://127.0.0.1:5000/auth"     
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
    res = requests.post(f"{API_URL}/signup", json=payload)

    click.echo(res.json())

# LOGIN COMMAND
@cli.command()
@click.option("--email", required=True, help="User Email")
@click.option("--password", required=True, help="User Password")
def login(email, password):
    """Login and save JWT token"""
    payload = {"email": email, "password": password}
    res = requests.post(f"{API_URL}/login", json=payload)

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
    res = requests.get(f"{API_URL}/user", headers=headers)

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
    res = requests.put(f"{API_URL}/user", json=payload, headers=headers)

    click.echo(res.json())

# ---- TASK COMMANDS ----

if __name__ == "__main__":
    cli()
