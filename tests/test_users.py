import pytest
from flask import Flask
from app import db, bcrypt, jwt     # ✅ import jwt
from app.models import User
from app.routes.auth_routes import auth_bp
from app.utils.jwtUtil import generate_jwt


@pytest.fixture
def app():
    """Create and configure a test Flask app."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'test_secret_key'

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)   # ✅ Initialize JWT manager here

    app.register_blueprint(auth_bp, url_prefix="/auth")

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Return Flask test client."""
    return app.test_client()


def create_user(name="John", email="john@example.com", password="123456"):
    """Helper to create a user directly in the DB."""
    user = User(name=name, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


# --- Tests ---

def test_signup_success(client):
    data = {"name": "Alice", "email": "alice@example.com", "password": "password123"}
    res = client.post("/auth/signup", json=data)
    assert res.status_code == 201
    assert b"User registered successfully" in res.data


def test_login_success(client):
    create_user(email="login@example.com", password="password123")
    data = {"email": "login@example.com", "password": "password123"}
    res = client.post("/auth/login", json=data)
    assert res.status_code == 200, f"Login failed: {res.get_json()}"
    assert "access_token" in res.get_json()


def test_login_invalid_credentials(client):
    create_user(email="wrong@example.com", password="correctpass")
    res = client.post("/auth/login", json={"email": "wrong@example.com", "password": "wrongpass"})
    assert res.status_code == 401


def test_get_current_user(client, app):
    with app.app_context():
        user = create_user(email="getme@example.com")
        token = generate_jwt(user_id=str(user.user_id))
    headers = {"Authorization": f"Bearer {token}"}
    res = client.get("/auth/user", headers=headers)
    assert res.status_code == 200
    assert res.get_json()["email"] == "getme@example.com"


def test_update_user_name(client, app):
    with app.app_context():
        user = create_user(email="update@example.com")
        token = generate_jwt(user_id=str(user.user_id))
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"name": "Updated Name"}
    res = client.put("/auth/user", json=payload, headers=headers)
    assert res.status_code == 200
    with app.app_context():
        updated_user = User.query.filter_by(email="update@example.com").first()
        assert updated_user.name == "Updated Name"
