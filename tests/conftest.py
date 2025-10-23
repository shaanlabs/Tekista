import os
import pytest
from app import create_app
from models import db, User

@pytest.fixture(scope="session")
def app():
    app = create_app()
    # Override config for tests
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        WTF_CSRF_ENABLED=False,
        SERVER_NAME='localhost'
    )
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def runner(app):
    return app.test_cli_runner()

@pytest.fixture()
def user(app):
    u = User(username='tester', email='tester@example.com', password_hash='')
    u.set_password('testpass123')
    db.session.add(u)
    db.session.commit()
    return u
