"""
Enterprise-Grade Features Module
Includes RBAC, Multi-org support, SSO/OAuth2, Audit logging, and encryption
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps

from flask import current_app, g, jsonify, request
from flask_login import current_user

from models import db

logger = logging.getLogger(__name__)

# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================


class Role(Enum):
    """User roles in the system"""

    ADMIN = "admin"
    PROJECT_MANAGER = "project_manager"
    TEAM_MEMBER = "team_member"
    VIEWER = "viewer"


class Permission(Enum):
    """Granular permissions"""

    # Task permissions
    VIEW_TASKS = "view_tasks"
    CREATE_TASKS = "create_tasks"
    EDIT_TASKS = "edit_tasks"
    DELETE_TASKS = "delete_tasks"
    ASSIGN_TASKS = "assign_tasks"

    # Project permissions
    VIEW_PROJECTS = "view_projects"
    CREATE_PROJECTS = "create_projects"
    EDIT_PROJECTS = "edit_projects"
    DELETE_PROJECTS = "delete_projects"
    MANAGE_PROJECT_MEMBERS = "manage_project_members"

    # Team permissions
    VIEW_TEAM = "view_team"
    MANAGE_TEAM = "manage_team"

    # Organization permissions
    MANAGE_ORGANIZATION = "manage_organization"
    MANAGE_ROLES = "manage_roles"
    VIEW_AUDIT_LOG = "view_audit_log"
    MANAGE_INTEGRATIONS = "manage_integrations"


# Default role permissions mapping
ROLE_PERMISSIONS = {
    Role.ADMIN: [p for p in Permission],  # All permissions
    Role.PROJECT_MANAGER: [
        Permission.VIEW_TASKS,
        Permission.CREATE_TASKS,
        Permission.EDIT_TASKS,
        Permission.DELETE_TASKS,
        Permission.ASSIGN_TASKS,
        Permission.VIEW_PROJECTS,
        Permission.CREATE_PROJECTS,
        Permission.EDIT_PROJECTS,
        Permission.MANAGE_PROJECT_MEMBERS,
        Permission.VIEW_TEAM,
        Permission.VIEW_AUDIT_LOG,
    ],
    Role.TEAM_MEMBER: [
        Permission.VIEW_TASKS,
        Permission.CREATE_TASKS,
        Permission.EDIT_TASKS,
        Permission.VIEW_PROJECTS,
        Permission.VIEW_TEAM,
    ],
    Role.VIEWER: [
        Permission.VIEW_TASKS,
        Permission.VIEW_PROJECTS,
        Permission.VIEW_TEAM,
    ],
}

# ============================================================================
# DECORATORS
# ============================================================================


def require_permission(permission):
    """Decorator to check if user has specific permission"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({"error": "Unauthorized"}), 401

            # Get user's organization
            org = current_user.organization
            if not org:
                return jsonify({"error": "User not in any organization"}), 403

            # Check permission
            if not current_user.has_permission(permission):
                logger.warning(
                    f"Permission denied for user {current_user.id}: {permission}"
                )
                return jsonify({"error": "Insufficient permissions"}), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def require_role(*roles):
    """Decorator to check if user has specific role"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({"error": "Unauthorized"}), 401

            if current_user.role not in roles:
                logger.warning(
                    f"Role denied for user {current_user.id}: required {roles}"
                )
                return jsonify({"error": "Insufficient role"}), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def audit_log(action, resource_type):
    """Decorator to log actions for audit trail"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            result = f(*args, **kwargs)

            # Log the action
            if current_user.is_authenticated:
                from enterprise.models import AuditLog

                audit = AuditLog(
                    user_id=current_user.id,
                    organization_id=current_user.organization_id,
                    action=action,
                    resource_type=resource_type,
                    resource_id=kwargs.get("id")
                    or kwargs.get("task_id")
                    or kwargs.get("project_id"),
                    details=request.get_json() if request.is_json else None,
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get("User-Agent"),
                )
                db.session.add(audit)
                db.session.commit()

            return result

        return decorated_function

    return decorator


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def get_user_organization():
    """Get current user's organization"""
    if not current_user.is_authenticated:
        return None
    return current_user.organization


def check_organization_access(org_id):
    """Check if current user has access to organization"""
    if not current_user.is_authenticated:
        return False

    if current_user.organization_id != org_id:
        return False

    return True


def filter_by_organization(query, model):
    """Filter query results by user's organization"""
    if not current_user.is_authenticated:
        return query.filter_by(id=-1)  # Return empty result

    if not hasattr(model, "organization_id"):
        return query

    return query.filter_by(organization_id=current_user.organization_id)


# ============================================================================
# ENCRYPTION UTILITIES
# ============================================================================

import base64
import hashlib

from cryptography.fernet import Fernet


class EncryptionManager:
    """Manages encryption/decryption of sensitive data"""

    def __init__(self):
        self.key = current_app.config.get("ENCRYPTION_KEY")
        if not self.key:
            raise ValueError("ENCRYPTION_KEY not configured")
        self.cipher = Fernet(self.key)

    def encrypt(self, data):
        """Encrypt data"""
        if isinstance(data, str):
            data = data.encode()
        return self.cipher.encrypt(data).decode()

    def decrypt(self, encrypted_data):
        """Decrypt data"""
        if isinstance(encrypted_data, str):
            encrypted_data = encrypted_data.encode()
        return self.cipher.decrypt(encrypted_data).decode()

    @staticmethod
    def generate_key():
        """Generate a new encryption key"""
        return Fernet.generate_key().decode()

    @staticmethod
    def hash_password(password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()


# ============================================================================
# API TOKEN MANAGEMENT
# ============================================================================

import secrets


class APITokenManager:
    """Manages secure API tokens for integrations"""

    @staticmethod
    def generate_token(user_id, organization_id, name, expires_in_days=90):
        """Generate a new API token"""
        from enterprise.models import APIToken

        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        api_token = APIToken(
            user_id=user_id,
            organization_id=organization_id,
            name=name,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days),
            last_used_at=None,
        )

        db.session.add(api_token)
        db.session.commit()

        return token  # Return unhashed token to user (only shown once)

    @staticmethod
    def verify_token(token):
        """Verify API token and return user"""
        from enterprise.models import APIToken

        token_hash = hashlib.sha256(token.encode()).hexdigest()
        api_token = APIToken.query.filter_by(token_hash=token_hash).first()

        if not api_token:
            return None

        if api_token.expires_at < datetime.utcnow():
            return None

        if api_token.is_revoked:
            return None

        # Update last used time
        api_token.last_used_at = datetime.utcnow()
        db.session.commit()

        return api_token.user

    @staticmethod
    def revoke_token(token_id):
        """Revoke an API token"""
        from enterprise.models import APIToken

        api_token = APIToken.query.get(token_id)
        if api_token:
            api_token.is_revoked = True
            db.session.commit()
            return True
        return False


# ============================================================================
# SSO/OAUTH2 UTILITIES
# ============================================================================


class OAuthProvider:
    """Base class for OAuth providers"""

    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_authorization_url(self, state):
        """Get OAuth authorization URL"""
        raise NotImplementedError

    def exchange_code_for_token(self, code):
        """Exchange authorization code for access token"""
        raise NotImplementedError

    def get_user_info(self, access_token):
        """Get user info from OAuth provider"""
        raise NotImplementedError


class GoogleOAuthProvider(OAuthProvider):
    """Google OAuth2 provider"""

    AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

    def get_authorization_url(self, state):
        """Get Google OAuth authorization URL"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
        }
        from urllib.parse import urlencode

        return f"{self.AUTHORIZATION_URL}?{urlencode(params)}"

    def exchange_code_for_token(self, code):
        """Exchange Google authorization code for token"""
        import requests

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }

        response = requests.post(self.TOKEN_URL, data=data)
        return response.json()

    def get_user_info(self, access_token):
        """Get user info from Google"""
        import requests

        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(self.USER_INFO_URL, headers=headers)
        return response.json()


class MicrosoftOAuthProvider(OAuthProvider):
    """Microsoft OAuth2 provider"""

    AUTHORIZATION_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
    TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    USER_INFO_URL = "https://graph.microsoft.com/v1.0/me"

    def get_authorization_url(self, state):
        """Get Microsoft OAuth authorization URL"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
        }
        from urllib.parse import urlencode

        return f"{self.AUTHORIZATION_URL}?{urlencode(params)}"

    def exchange_code_for_token(self, code):
        """Exchange Microsoft authorization code for token"""
        import requests

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
            "scope": "openid email profile",
        }

        response = requests.post(self.TOKEN_URL, data=data)
        return response.json()

    def get_user_info(self, access_token):
        """Get user info from Microsoft"""
        import requests

        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(self.USER_INFO_URL, headers=headers)
        return response.json()


# ============================================================================
# DATA RETENTION POLICY
# ============================================================================


class DataRetentionPolicy:
    """Manages data retention and deletion policies"""

    @staticmethod
    def get_retention_days(organization_id):
        """Get data retention period for organization"""
        from enterprise.models import Organization

        org = Organization.query.get(organization_id)
        if org:
            return org.data_retention_days
        return 365  # Default 1 year

    @staticmethod
    def cleanup_old_data(organization_id):
        """Delete data older than retention period"""
        from enterprise.models import AuditLog

        retention_days = DataRetentionPolicy.get_retention_days(organization_id)
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        deleted_count = AuditLog.query.filter(
            AuditLog.organization_id == organization_id,
            AuditLog.created_at < cutoff_date,
        ).delete()

        db.session.commit()
        logger.info(f"Deleted {deleted_count} audit logs for org {organization_id}")

        return deleted_count

    @staticmethod
    def schedule_cleanup():
        """Schedule periodic cleanup of old data"""
        from apscheduler.schedulers.background import BackgroundScheduler

        scheduler = BackgroundScheduler()
        scheduler.add_job(
            func=DataRetentionPolicy._cleanup_all_organizations,
            trigger="cron",
            hour=2,
            minute=0,
        )
        scheduler.start()

    @staticmethod
    def _cleanup_all_organizations():
        """Cleanup old data for all organizations"""
        from enterprise.models import Organization

        organizations = Organization.query.all()
        for org in organizations:
            DataRetentionPolicy.cleanup_old_data(org.id)
