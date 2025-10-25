"""
Tests for AI routes.

Tests AI assistance, estimation, risk prediction, and chat features.
"""
import json

import pytest


@pytest.mark.ai
@pytest.mark.integration
class TestAIRoutes:
    """Test AI endpoint functionality."""

    def test_ai_estimate_duration(self, client, task, user):
        """Test POST /ai/estimate-duration."""
        with client.session_transaction() as session:
            session['user_id'] = user.id
            session['_fresh'] = True

        resp = client.post('/ai/estimate-duration', json={
            'task_id': task.id,
            'description': task.description
        })
        # Should return 200 or handle gracefully
        assert resp.status_code in (200, 503)

    def test_ai_risks(self, client, project, user):
        """Test GET /ai/risks."""
        with client.session_transaction() as session:
            session['user_id'] = user.id
            session['_fresh'] = True

        resp = client.get(f'/ai/risks?project_id={project.id}')
        assert resp.status_code in (200, 503)

    def test_ai_summary(self, client, project, user):
        """Test GET /ai/summary."""
        with client.session_transaction() as session:
            session['user_id'] = user.id
            session['_fresh'] = True

        resp = client.get(f'/ai/summary?project_id={project.id}')
        assert resp.status_code in (200, 503)

    def test_ai_chat(self, client, user):
        """Test POST /ai/chat."""
        with client.session_transaction() as session:
            session['user_id'] = user.id
            session['_fresh'] = True

        resp = client.post('/ai/chat', json={
            'message': 'What is my workload?'
        })
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'reply' in data

    def test_ai_create_task(self, client, project, manager_user):
        """Test POST /ai/create-task."""
        with client.session_transaction() as session:
            session['user_id'] = manager_user.id
            session['_fresh'] = True

        resp = client.post('/ai/create-task', json={
            'project_id': project.id,
            'prompt': 'Create a task to implement user authentication'
        })
        assert resp.status_code in (200, 201, 503)

    def test_ai_workload(self, client, user):
        """Test GET /ai/workload."""
        with client.session_transaction() as session:
            session['user_id'] = user.id
            session['_fresh'] = True

        resp = client.get('/ai/workload')
        assert resp.status_code in (200, 503)

    def test_ai_suggestions(self, client, user):
        """Test GET /ai/suggestions."""
        with client.session_transaction() as session:
            session['user_id'] = user.id
            session['_fresh'] = True

        resp = client.get('/ai/suggestions')
        assert resp.status_code in (200, 503)


@pytest.mark.ai
class TestAIAuthentication:
    """Test AI endpoint authentication."""

    def test_ai_requires_auth(self, client):
        """Test AI endpoints require authentication."""
        resp = client.post('/ai/chat', json={'message': 'test'})
        assert resp.status_code in (302, 303, 401, 403)


@pytest.mark.ai
class TestAIPMAgent:
    """Test AI PM agent features."""

    def test_pm_decompose(self, client, manager_user):
        """Test POST /ai/pm/decompose."""
        with client.session_transaction() as session:
            session['user_id'] = manager_user.id
            session['_fresh'] = True

        resp = client.post('/ai/pm/decompose', json={
            'goal': 'Build a user authentication system'
        })
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'plan' in data

    def test_pm_apply_plan(self, client, project, manager_user):
        """Test POST /ai/pm/apply-plan."""
        with client.session_transaction() as session:
            session['user_id'] = manager_user.id
            session['_fresh'] = True

        resp = client.post('/ai/pm/apply-plan', json={
            'project_id': project.id,
            'plan': {
                'goal': 'Implement feature',
                'tasks': [
                    {'title': 'Task 1', 'desc': 'Description', 'priority': 'High'}
                ]
            }
        })
        assert resp.status_code == 200

    def test_pm_apply_plan_forbidden_for_member(self, client, project, user):
        """Test PM apply-plan requires Manager role."""
        with client.session_transaction() as session:
            session['user_id'] = user.id
            session['_fresh'] = True

        resp = client.post('/ai/pm/apply-plan', json={
            'project_id': project.id,
            'plan': {'tasks': []}
        })
        assert resp.status_code == 403
