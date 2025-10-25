"""
Pytest configuration and shared fixtures.

This module provides common fixtures and setup for all tests.
"""
import os
import sys
from datetime import datetime, timedelta

import pytest

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import AuditLog, Notification, Project, Role, Task, User, db


@pytest.fixture(scope="session")
def app():
    """Create and configure test application."""
    test_app = create_app()
    # Override config for tests
    test_app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        WTF_CSRF_ENABLED=False,
        SERVER_NAME='localhost',
        USE_CELERY=False,  # Disable Celery for tests
    )
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture()
def runner(app):
    """Create CLI test runner."""
    return app.test_cli_runner()


@pytest.fixture()
def admin_role(app):
    """Create Admin role."""
    role = Role.query.filter_by(name='Admin').first()
    if not role:
        role = Role(name='Admin', description='Administrator')
        db.session.add(role)
        db.session.commit()
    return role


@pytest.fixture()
def manager_role(app):
    """Create Manager role."""
    role = Role.query.filter_by(name='Manager').first()
    if not role:
        role = Role(name='Manager', description='Project Manager')
        db.session.add(role)
        db.session.commit()
    return role


@pytest.fixture()
def member_role(app):
    """Create Member role."""
    role = Role.query.filter_by(name='Member').first()
    if not role:
        role = Role(name='Member', description='Team Member')
        db.session.add(role)
        db.session.commit()
    return role


@pytest.fixture()
def user(app, member_role):
    """Create test user."""
    test_user = User(username='tester', email='tester@example.com')
    test_user.set_password('testpass123')
    test_user.role = member_role
    db.session.add(test_user)
    db.session.commit()
    return test_user


@pytest.fixture()
def admin_user(app, admin_role):
    """Create admin user."""
    admin = User(username='admin', email='admin@example.com')
    admin.set_password('admin123')
    admin.role = admin_role
    db.session.add(admin)
    db.session.commit()
    return admin


@pytest.fixture()
def manager_user(app, manager_role):
    """Create manager user."""
    manager = User(username='manager', email='manager@example.com')
    manager.set_password('manager123')
    manager.role = manager_role
    db.session.add(manager)
    db.session.commit()
    return manager


@pytest.fixture()
def project(app, manager_user):
    """Create test project."""
    proj = Project(
        title='Test Project',
        description='Test project description',
        deadline=(datetime.utcnow() + timedelta(days=30)).date()
    )
    proj.users.append(manager_user)
    db.session.add(proj)
    db.session.commit()
    return proj


@pytest.fixture()
def task(app, project, user):
    """Create test task."""
    test_task = Task(
        title='Test Task',
        description='Test task description',
        priority='Normal',
        status='To Do',
        project=project
    )
    test_task.assignees.append(user)
    db.session.add(test_task)
    db.session.commit()
    return test_task


@pytest.fixture()
def auth_headers(client, user):
    """Get auth headers for API requests."""
    with client.session_transaction() as session:
        session['user_id'] = user.id
        session['_fresh'] = True
    return {}
