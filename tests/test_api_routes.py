"""
Tests for API routes.

Tests RESTful API endpoints for projects, tasks, and other resources.
"""

import json

import pytest

from models import Project, Task, db


@pytest.mark.api
@pytest.mark.integration
class TestProjectAPI:
    """Test Project API endpoints."""

    def test_list_projects(self, client, project, user):
        """Test GET /api/projects."""
        with client.session_transaction() as session:
            session["user_id"] = user.id
            session["_fresh"] = True

        resp = client.get("/api/projects")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert isinstance(data, list)

    def test_create_project(self, client, manager_user):
        """Test POST /api/projects."""
        with client.session_transaction() as session:
            session["user_id"] = manager_user.id
            session["_fresh"] = True

        resp = client.post(
            "/api/projects",
            json={
                "title": "New API Project",
                "description": "Created via API",
                "deadline": "2025-12-31",
            },
        )
        assert resp.status_code == 201
        data = json.loads(resp.data)
        assert data["title"] == "New API Project"

    def test_get_project_detail(self, client, project, user):
        """Test GET /api/projects/<id>."""
        with client.session_transaction() as session:
            session["user_id"] = user.id
            session["_fresh"] = True

        resp = client.get(f"/api/projects/{project.id}")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["title"] == project.title

    def test_update_project(self, client, project, manager_user):
        """Test PATCH /api/projects/<id>."""
        with client.session_transaction() as session:
            session["user_id"] = manager_user.id
            session["_fresh"] = True

        resp = client.patch(
            f"/api/projects/{project.id}", json={"title": "Updated Title"}
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["title"] == "Updated Title"

    def test_delete_project(self, client, project, manager_user):
        """Test DELETE /api/projects/<id>."""
        with client.session_transaction() as session:
            session["user_id"] = manager_user.id
            session["_fresh"] = True

        resp = client.delete(f"/api/projects/{project.id}")
        assert resp.status_code == 200

        # Verify project is deleted
        deleted_project = db.session.get(Project, project.id)
        assert deleted_project is None


@pytest.mark.api
@pytest.mark.integration
class TestTaskAPI:
    """Test Task API endpoints."""

    def test_list_tasks(self, client, task, user):
        """Test GET /api/tasks."""
        with client.session_transaction() as session:
            session["user_id"] = user.id
            session["_fresh"] = True

        resp = client.get("/api/tasks")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert isinstance(data, list)

    def test_create_task(self, client, project, manager_user, user):
        """Test POST /api/tasks."""
        with client.session_transaction() as session:
            session["user_id"] = manager_user.id
            session["_fresh"] = True

        resp = client.post(
            "/api/tasks",
            json={
                "title": "New API Task",
                "description": "Created via API",
                "project_id": project.id,
                "assignees": [user.id],
                "priority": "High",
            },
        )
        assert resp.status_code == 201
        data = json.loads(resp.data)
        assert data["title"] == "New API Task"

    def test_get_task_detail(self, client, task, user):
        """Test GET /api/tasks/<id>."""
        with client.session_transaction() as session:
            session["user_id"] = user.id
            session["_fresh"] = True

        resp = client.get(f"/api/tasks/{task.id}")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["title"] == task.title

    def test_update_task_status(self, client, task, user):
        """Test PATCH /api/tasks/<id> to update status."""
        with client.session_transaction() as session:
            session["user_id"] = user.id
            session["_fresh"] = True

        resp = client.patch(f"/api/tasks/{task.id}", json={"status": "In Progress"})
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["status"] == "In Progress"

    def test_delete_task(self, client, task, manager_user):
        """Test DELETE /api/tasks/<id>."""
        with client.session_transaction() as session:
            session["user_id"] = manager_user.id
            session["_fresh"] = True

        resp = client.delete(f"/api/tasks/{task.id}")
        assert resp.status_code == 200

        # Verify task is deleted
        deleted_task = db.session.get(Task, task.id)
        assert deleted_task is None


@pytest.mark.api
class TestAPIAuthentication:
    """Test API authentication requirements."""

    def test_api_requires_auth(self, client):
        """Test API endpoints require authentication."""
        # Try to access without auth
        resp = client.get("/api/projects")
        # Should redirect to login or return 401/403
        assert resp.status_code in (302, 303, 401, 403)

    def test_api_with_invalid_data(self, client, manager_user):
        """Test API with invalid data."""
        with client.session_transaction() as session:
            session["user_id"] = manager_user.id
            session["_fresh"] = True

        # Missing required field
        resp = client.post("/api/projects", json={"description": "Missing title"})
        assert resp.status_code == 400


@pytest.mark.api
class TestAPIEdgeCases:
    """Test API edge cases and error handling."""

    def test_get_nonexistent_project(self, client, user):
        """Test GET with non-existent project ID."""
        with client.session_transaction() as session:
            session["user_id"] = user.id
            session["_fresh"] = True

        resp = client.get("/api/projects/99999")
        assert resp.status_code == 404

    def test_update_nonexistent_task(self, client, user):
        """Test PATCH with non-existent task ID."""
        with client.session_transaction() as session:
            session["user_id"] = user.id
            session["_fresh"] = True

        resp = client.patch("/api/tasks/99999", json={"title": "New Title"})
        assert resp.status_code == 404
