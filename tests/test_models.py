"""
Tests for database models.

Tests User, Project, Task, Role, and other model functionality.
"""

from datetime import datetime, timedelta

import pytest

from models import AuditLog, Comment, Project, Role, Task, User, db


@pytest.mark.unit
@pytest.mark.db
class TestUserModel:
    """Test User model."""

    def test_user_creation(self, app):
        """Test creating a user."""
        user = User(username="testuser", email="test@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()

        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.check_password("password123")
        assert not user.check_password("wrongpassword")

    def test_user_password_hash(self, user):
        """Test password hashing."""
        assert user.password_hash is not None
        assert user.password_hash != "testpass123"
        assert user.check_password("testpass123")

    def test_user_role_assignment(self, user, admin_role):
        """Test assigning roles to users."""
        user.role = admin_role
        db.session.commit()
        assert user.role.name == "Admin"

    def test_user_repr(self, user):
        """Test User __repr__ method."""
        repr_str = repr(user)
        assert "User" in repr_str
        assert user.username in repr_str


@pytest.mark.unit
@pytest.mark.db
class TestProjectModel:
    """Test Project model."""

    def test_project_creation(self, app, manager_user):
        """Test creating a project."""
        project = Project(
            title="New Project",
            description="Project description",
            deadline=(datetime.utcnow() + timedelta(days=30)).date(),
        )
        project.users.append(manager_user)
        db.session.add(project)
        db.session.commit()

        assert project.id is not None
        assert project.title == "New Project"
        assert manager_user in project.users

    def test_project_progress(self, project, user):
        """Test project progress calculation."""
        # Create tasks with different statuses
        task1 = Task(title="Task 1", status="Completed", project=project)
        task2 = Task(title="Task 2", status="In Progress", project=project)
        task3 = Task(title="Task 3", status="To Do", project=project)
        db.session.add_all([task1, task2, task3])
        db.session.commit()

        progress = project.progress
        # 1 out of 3 tasks completed = 33.33%
        assert progress > 0
        assert progress < 100

    def test_project_users_relationship(self, project, user, manager_user):
        """Test project-users many-to-many relationship."""
        project.users.append(user)
        db.session.commit()

        assert user in project.users
        assert manager_user in project.users
        assert project in user.projects


@pytest.mark.unit
@pytest.mark.db
class TestTaskModel:
    """Test Task model."""

    def test_task_creation(self, project, user):
        """Test creating a task."""
        task = Task(
            title="Test Task",
            description="Task description",
            priority="High",
            status="To Do",
            project=project,
        )
        task.assignees.append(user)
        db.session.add(task)
        db.session.commit()

        assert task.id is not None
        assert task.title == "Test Task"
        assert task.priority == "High"
        assert user in task.assignees

    def test_task_status_values(self, task):
        """Test task status values."""
        valid_statuses = ["To Do", "In Progress", "Completed"]
        for status in valid_statuses:
            task.status = status
            db.session.commit()
            assert task.status == status

    def test_task_assignees_relationship(self, task, user, manager_user):
        """Test task-assignees many-to-many relationship."""
        task.assignees.append(manager_user)
        db.session.commit()

        assert user in task.assignees
        assert manager_user in task.assignees
        assert task in user.assigned_tasks

    def test_task_comments(self, task, user):
        """Test task comments relationship."""
        comment = Comment(body="Test comment", author_id=user.id, task_id=task.id)
        db.session.add(comment)
        db.session.commit()

        assert comment in task.comments
        assert comment.author == user


@pytest.mark.unit
@pytest.mark.db
class TestRoleModel:
    """Test Role model."""

    def test_role_creation(self, app):
        """Test creating a role."""
        role = Role(name="Developer", description="Software Developer")
        db.session.add(role)
        db.session.commit()

        assert role.id is not None
        assert role.name == "Developer"

    def test_role_users_relationship(self, admin_role, admin_user, manager_user):
        """Test role-users relationship."""
        manager_user.role = admin_role
        db.session.commit()

        assert admin_user in admin_role.users
        assert manager_user in admin_role.users


@pytest.mark.unit
@pytest.mark.db
class TestAuditLog:
    """Test AuditLog model."""

    def test_audit_log_creation(self, app, user):
        """Test creating an audit log entry."""
        log = AuditLog(
            actor_id=user.id,
            action="create",
            target_type="project",
            target_id=1,
            meta="Test action",
        )
        db.session.add(log)
        db.session.commit()

        assert log.id is not None
        assert log.actor_id == user.id
        assert log.action == "create"
