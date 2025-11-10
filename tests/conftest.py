import os
import sys
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, db
from app.models import User
from app.utils.jwtUtil import generate_jwt


@pytest.fixture()
def test_client():
    """Fixture for Flask test client, app context, and test user."""
    app = create_app(testing=True)
    app.config.update({
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "TESTING": True
    })

    with app.app_context():
        db.create_all()
        client = app.test_client()

        # ✅ Create a default user for testing
        user = User(name="Test User", email="test@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()

        yield client, app, user   # ✅ return exactly 3 values

        db.session.remove()
        db.drop_all()


@pytest.fixture()
def auth_header(test_client):
    """Fixture to generate auth header for the test user."""
    client, app, user = test_client
    token = generate_jwt(user_id=str(user.user_id))
    return {"Authorization": f"Bearer {token}"}
