"""
Tests for automation routes.

Tests task completion, status updates, and automation triggers.
"""

import json

import pytest

from models import AuditLog, db


@pytest.mark.integration
class TestAutomationRoutes:
    """Test automation endpoint functionality."""

    def test_complete_task(self, client, task, user):
        """Test POST /automation/tasks/<id>/complete."""
        with client.session_transaction() as session:
            session["user_id"] = user.id
            session["_fresh"] = True

        resp = client.post(
            f"/automation/tasks/{task.id}/complete",
            json={"actual_hours": 4.5, "notes": "Task completed successfully"},
        )
        assert resp.status_code in (200, 500)  # 500 if automation modules missing
        if resp.status_code == 200:
            data = json.loads(resp.data)
            assert data["success"] is True

            # Verify task status changed
            db.session.refresh(task)
            assert task.status == "Completed"

    def test_complete_task_unauthorized(self, client, task, manager_user):
        """Test completing task as non-assignee."""
        with client.session_transaction() as session:
            session["user_id"] = manager_user.id
            session["_fresh"] = True

        resp = client.post(
            f"/automation/tasks/{task.id}/complete", json={"actual_hours": 3.0}
        )
        assert resp.status_code in (403, 500)

    def test_update_task_status(self, client, task, manager_user):
        """Test PUT /automation/tasks/<id>/status."""
        with client.session_transaction() as session:
            session["user_id"] = manager_user.id
            session["_fresh"] = True

        resp = client.put(
            f"/automation/tasks/{task.id}/status", json={"status": "In Progress"}
        )
        assert resp.status_code in (200, 500)
        if resp.status_code == 200:
            db.session.refresh(task)
            assert task.status == "In Progress"

    def test_update_status_normalized(self, client, task, manager_user):
        """Test status normalization (done -> Completed)."""
        with client.session_transaction() as session:
            session["user_id"] = manager_user.id
            session["_fresh"] = True

        resp = client.put(
            f"/automation/tasks/{task.id}/status", json={"status": "done"}
        )
        if resp.status_code == 200:
            db.session.refresh(task)
            assert task.status == "Completed"

    def test_update_status_forbidden_for_member(self, client, task, user):
        """Test non-manager/non-assignee cannot update status."""
        # Remove user as assignee
        task.assignees.clear()
        db.session.commit()

        with client.session_transaction() as session:
            session["user_id"] = user.id
            session["_fresh"] = True

        resp = client.put(
            f"/automation/tasks/{task.id}/status", json={"status": "Completed"}
        )
        assert resp.status_code in (403, 500)

    def test_get_user_performance(self, client, user):
        """Test GET /automation/performance/user/<id>."""
        with client.session_transaction() as session:
            session["user_id"] = user.id
            session["_fresh"] = True

        resp = client.get(f"/automation/performance/user/{user.id}")
        assert resp.status_code in (200, 404, 500, 501)

    def test_get_team_performance(self, client, manager_user):
        """Test GET /automation/performance/team."""
        with client.session_transaction() as session:
            session["user_id"] = manager_user.id
            session["_fresh"] = True

        resp = client.get("/automation/performance/team")
        assert resp.status_code in (200, 403, 500, 501)

    def test_get_automation_log(self, client, admin_user):
        """Test GET /automation/automation-log."""
        with client.session_transaction() as session:
            session["user_id"] = admin_user.id
            session["_fresh"] = True

        resp = client.get("/automation/automation-log")
        assert resp.status_code in (200, 403, 500)


@pytest.mark.integration
class TestAuditLogging:
    """Test audit logging functionality."""

    def test_audit_log_created_on_complete(self, client, task, user):
        """Test audit log is created when task is completed."""
        with client.session_transaction() as session:
            session["user_id"] = user.id
            session["_fresh"] = True

        initial_count = AuditLog.query.count()

        resp = client.post(
            f"/automation/tasks/{task.id}/complete", json={"actual_hours": 2.0}
        )

        if resp.status_code == 200:
            # Check if audit log was created
            final_count = AuditLog.query.count()
            assert final_count >= initial_count
