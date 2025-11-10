import os
import sys
import pytest

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, db

@pytest.fixture()
def client():
    app = create_app(testing=True)

    with app.app_context():
        db.create_all()
        yield app.test_client()

        db.session.remove()
        db.drop_all()

