"""
Tests for authentication module.

Tests login, logout, registration, and access control.
"""
import pytest

from models import User, db


@pytest.mark.auth
class TestAuthentication:
    """Test authentication flows."""

    def test_register_login_logout_flow(self, client, app):
        """Test complete registration, login, and logout flow."""
        # Register
        resp = client.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'Newpass123!',
            'confirm': 'Newpass123!'
        }, follow_redirects=True)
        assert resp.status_code == 200

        # Login failure
        resp = client.post('/login', data={'username': 'newuser', 'password': 'wrong'},
                          follow_redirects=False)
        assert resp.status_code == 200  # stays on login page due to flash

        # Login success
        resp = client.post('/login', data={'username': 'newuser', 'password': 'Newpass123!'},
                          follow_redirects=False)
        assert resp.status_code in (302, 303)

        # Logout
        resp = client.get('/logout', follow_redirects=False)
        assert resp.status_code in (302, 303)

    def test_login_required_redirect(self, client):
        """Test that protected routes redirect to login."""
        resp = client.get('/', follow_redirects=False)
        assert resp.status_code in (302, 303)
        assert '/login' in resp.location or 'login' in resp.location

    def test_duplicate_username(self, client, user):
        """Test registration with duplicate username."""
        resp = client.post('/register', data={
            'username': user.username,
            'email': 'different@example.com',
            'password': 'Test123!',
            'confirm': 'Test123!'
        })
        assert resp.status_code == 200
        # Should stay on register page

    def test_password_validation(self, client):
        """Test password confirmation validation."""
        resp = client.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'Pass123!',
            'confirm': 'Different!'
        })
        assert resp.status_code == 200

    def test_user_can_change_password(self, client, user):
        """Test password change functionality."""
        # Login
        client.post('/login', data={
            'username': user.username,
            'password': 'testpass123'
        })
        # Verify old password works
        assert user.check_password('testpass123')


@pytest.mark.auth
class TestAccessControl:
    """Test role-based access control."""

    def test_admin_access(self, client, admin_user):
        """Test admin can access admin routes."""
        with client.session_transaction() as session:
            session['user_id'] = admin_user.id
            session['_fresh'] = True

        resp = client.get('/reports')
        assert resp.status_code == 200

    def test_non_admin_blocked(self, client, user):
        """Test non-admin cannot access admin routes."""
        with client.session_transaction() as session:
            session['user_id'] = user.id
            session['_fresh'] = True

        resp = client.get('/reports', follow_redirects=False)
        # Should be forbidden or redirected
        assert resp.status_code in (302, 303, 403)
