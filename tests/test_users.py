import pytest
from flask import Flask
from app import db, bcrypt, jwt
from app.models import User
from app.routes.auth_routes import auth_bp
from app.utils.jwtUtil import generate_jwt


def signup(client, name="John", email="john@example.com", password="secret123"):
    return client.post(
        "/auth/signup",
        json={"name": name, "email": email, "password": password},
    )


def login(client, email="john@example.com", password="secret123"):
    return client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'test_secret_key'

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    app.register_blueprint(auth_bp, url_prefix="/auth")

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def create_user(name="John", email="john@example.com", password="123456"):
    user = User(name=name, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


# ---------------------- TESTS ---------------------- #

def test_get_current_user_unauthorized(client):
    res = client.get("/auth/user")
    assert res.status_code == 401


def test_signup_duplicate_email(client):
    signup(client)
    res = signup(client)
    assert res.status_code == 400
    assert "Email already registered" in res.json["message"]


def test_signup_invalid_schema(client):
    res = client.post("/auth/signup", json={"email": "bad"})
    assert res.status_code == 400
    assert "errors" in res.json


def test_signup_success(client):
    data = {"name": "Alice", "email": "alice@example.com", "password": "password123"}
    res = client.post("/auth/signup", json=data)
    assert res.status_code == 201
    assert b"User registered successfully" in res.data


def test_login_success(client, app):
    with app.app_context():
        create_user(email="login@example.com", password="password123")

    data = {"email": "login@example.com", "password": "password123"}
    res = client.post("/auth/login", json=data)

    assert res.status_code == 200
    assert "access_token" in res.json


def test_login_invalid_credentials(client, app):
    with app.app_context():
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
    assert res.json["email"] == "getme@example.com"


def test_update_user_name(client, app):
    with app.app_context():
        user = create_user(email="update@example.com")
        token = generate_jwt(user_id=str(user.user_id))

    headers = {"Authorization": f"Bearer {token}"}
    payload = {"name": "Updated Name"}

    res = client.put("/auth/user", json=payload, headers=headers)
    assert res.status_code == 200

    with app.app_context():
        updated = User.query.filter_by(email="update@example.com").first()
        assert updated.name == "Updated Name"


def test_update_user_password(client, app):
    signup(client)
    login_res = login(client)
    token = login_res.json["access_token"]

    res = client.put(
        "/auth/user",
        headers={"Authorization": f"Bearer {token}"},
        json={"password": "newpass"},
    )

    assert res.status_code == 200

    with app.app_context():
        user = User.query.filter_by(email="john@example.com").first()
        assert user.check_password("newpass")


def test_update_user_invalid_token(client):
    res = client.put(
        "/auth/user",
        headers={"Authorization": "Bearer BADTOKEN"},
        json={"name": "test"},
    )

    assert res.status_code in (401, 422)
