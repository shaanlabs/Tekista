"""
Enterprise Models for RBAC, Multi-org, SSO, and Audit logging
"""

import json
from datetime import datetime, timedelta

from sqlalchemy.dialects.postgresql import JSON

from models import db

# ============================================================================
# ORGANIZATION & MULTI-TENANCY
# ============================================================================

class Organization(db.Model):
    """Organization/Workspace model for multi-tenancy"""
    __tablename__ = "organization"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    slug = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    logo_url = db.Column(db.String(500))
    
    # Settings
    data_retention_days = db.Column(db.Integer, default=365)
    max_users = db.Column(db.Integer, default=100)
    max_projects = db.Column(db.Integer, default=50)
    
    # Features
    sso_enabled = db.Column(db.Boolean, default=False)
    api_enabled = db.Column(db.Boolean, default=True)
    audit_logging_enabled = db.Column(db.Boolean, default=True)
    encryption_enabled = db.Column(db.Boolean, default=True)
    
    # Subscription
    subscription_tier = db.Column(db.String(50), default="free")  # free, pro, enterprise
    subscription_expires_at = db.Column(db.DateTime)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='organization', lazy='dynamic', cascade='all, delete-orphan')
    projects = db.relationship('Project', backref='organization', lazy='dynamic', cascade='all, delete-orphan')
    api_tokens = db.relationship('APIToken', backref='organization', lazy='dynamic', cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', backref='organization', lazy='dynamic', cascade='all, delete-orphan')
    custom_roles = db.relationship('CustomRole', backref='organization', lazy='dynamic', cascade='all, delete-orphan')
    oauth_configs = db.relationship('OAuthConfig', backref='organization', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Organization {self.name}>'
    
    def is_subscription_active(self):
        """Check if subscription is active"""
        if not self.subscription_expires_at:
            return True
        return self.subscription_expires_at > datetime.utcnow()
    
    def get_user_count(self):
        """Get number of users in organization"""
        return self.users.count()
    
    def can_add_user(self):
        """Check if organization can add more users"""
        return self.get_user_count() < self.max_users

# ============================================================================
# ROLE-BASED ACCESS CONTROL
# ============================================================================

class Role(db.Model):
    """User role model"""
    __tablename__ = "role"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Relationships
    users = db.relationship('User', backref='role_obj', lazy='dynamic')
    permissions = db.relationship('Permission', secondary='role_permissions', backref='roles')
    
    def __repr__(self):
        return f'<Role {self.name}>'

class Permission(db.Model):
    """Permission model"""
    __tablename__ = "permission"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # tasks, projects, organization, etc.
    
    def __repr__(self):
        return f'<Permission {self.name}>'

# Association table for roles and permissions
role_permissions = db.Table(
    'role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'), primary_key=True)
)

class CustomRole(db.Model):
    """Custom role for organization-specific roles"""
    __tablename__ = "custom_role"
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    permissions = db.Column(JSON, default={})  # Store permissions as JSON
    
    # Relationships
    users = db.relationship('User', backref='custom_role_obj', lazy='dynamic')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<CustomRole {self.name}>'

# ============================================================================
# USER EXTENSIONS FOR ENTERPRISE
# ============================================================================

class UserOrganizationRole(db.Model):
    """User's role within an organization"""
    __tablename__ = "user_organization_role"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # admin, project_manager, team_member, viewer
    custom_role_id = db.Column(db.Integer, db.ForeignKey('custom_role.id'))
    
    # Custom permissions override
    custom_permissions = db.Column(JSON, default={})
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'organization_id', name='unique_user_org'),
    )
    
    def __repr__(self):
        return f'<UserOrganizationRole {self.user_id} - {self.organization_id}>'

# ============================================================================
# API TOKEN MANAGEMENT
# ============================================================================

class APIToken(db.Model):
    """API token for secure integrations"""
    __tablename__ = "api_token"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    
    name = db.Column(db.String(255), nullable=False)
    token_hash = db.Column(db.String(255), nullable=False, unique=True)
    
    # Token metadata
    last_used_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_revoked = db.Column(db.Boolean, default=False)
    
    # Scopes/Permissions
    scopes = db.Column(JSON, default=["read"])
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='api_tokens')
    
    def __repr__(self):
        return f'<APIToken {self.name}>'
    
    def is_valid(self):
        """Check if token is valid"""
        return (
            not self.is_revoked and
            self.expires_at > datetime.utcnow()
        )

# ============================================================================
# SSO & OAUTH
# ============================================================================

class OAuthConfig(db.Model):
    """OAuth configuration for organization"""
    __tablename__ = "oauth_config"
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    
    provider = db.Column(db.String(50), nullable=False)  # google, microsoft, slack
    client_id = db.Column(db.String(255), nullable=False)
    client_secret = db.Column(db.String(255), nullable=False)  # Should be encrypted
    redirect_uri = db.Column(db.String(500))
    
    is_enabled = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('organization_id', 'provider', name='unique_org_provider'),
    )
    
    def __repr__(self):
        return f'<OAuthConfig {self.provider}>'

class OAuthAccount(db.Model):
    """User's OAuth account"""
    __tablename__ = "oauth_account"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    provider = db.Column(db.String(50), nullable=False)  # google, microsoft, slack
    provider_user_id = db.Column(db.String(255), nullable=False)
    provider_email = db.Column(db.String(255))
    
    access_token = db.Column(db.Text)  # Should be encrypted
    refresh_token = db.Column(db.Text)  # Should be encrypted
    token_expires_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='oauth_accounts')
    
    __table_args__ = (
        db.UniqueConstraint('provider', 'provider_user_id', name='unique_provider_account'),
    )
    
    def __repr__(self):
        return f'<OAuthAccount {self.provider}>'

# ============================================================================
# AUDIT LOGGING
# ============================================================================

class AuditLog(db.Model):
    """Audit log for tracking all user actions"""
    __tablename__ = "audit_log"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    
    action = db.Column(db.String(100), nullable=False)  # create, update, delete, view, etc.
    resource_type = db.Column(db.String(50), nullable=False)  # task, project, user, etc.
    resource_id = db.Column(db.Integer)
    
    # Change tracking
    old_values = db.Column(JSON)
    new_values = db.Column(JSON)
    details = db.Column(JSON)
    
    # Request metadata
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(500))
    
    # Status
    status = db.Column(db.String(20), default="success")  # success, failure
    error_message = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = db.relationship('User', backref='audit_logs')
    
    def __repr__(self):
        return f'<AuditLog {self.action} {self.resource_type}>'
    
    @staticmethod
    def log_action(user_id, organization_id, action, resource_type, resource_id=None,
                   old_values=None, new_values=None, details=None, ip_address=None,
                   user_agent=None, status="success", error_message=None):
        """Create audit log entry"""
        audit = AuditLog(
            user_id=user_id,
            organization_id=organization_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_message=error_message
        )
        db.session.add(audit)
        db.session.commit()
        return audit

# ============================================================================
# DATA ENCRYPTION
# ============================================================================

class EncryptedField(db.TypeDecorator):
    """SQLAlchemy type for encrypted fields"""
    impl = db.String
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        """Encrypt data before storing"""
        if value is None:
            return None
        
        from enterprise import EncryptionManager
        try:
            manager = EncryptionManager()
            return manager.encrypt(value)
        except Exception as e:
            # If encryption fails, store as-is (for backward compatibility)
            return value
    
    def process_result_value(self, value, dialect):
        """Decrypt data after retrieving"""
        if value is None:
            return None
        
        from enterprise import EncryptionManager
        try:
            manager = EncryptionManager()
            return manager.decrypt(value)
        except Exception as e:
            # If decryption fails, return as-is
            return value

# ============================================================================
# INTEGRATION & WEBHOOKS
# ============================================================================

class Integration(db.Model):
    """Third-party integration configuration"""
    __tablename__ = "integration"
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    
    name = db.Column(db.String(100), nullable=False)
    service_type = db.Column(db.String(50), nullable=False)  # slack, github, jira, etc.
    
    # Configuration
    config = db.Column(JSON)  # Service-specific configuration
    webhook_url = db.Column(db.String(500))
    webhook_secret = db.Column(db.String(255))
    
    is_enabled = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', backref='integrations')
    
    def __repr__(self):
        return f'<Integration {self.service_type}>'

class Webhook(db.Model):
    """Webhook event log"""
    __tablename__ = "webhook"
    
    id = db.Column(db.Integer, primary_key=True)
    integration_id = db.Column(db.Integer, db.ForeignKey('integration.id'), nullable=False)
    
    event_type = db.Column(db.String(100), nullable=False)
    payload = db.Column(JSON)
    
    status = db.Column(db.String(20), default="pending")  # pending, sent, failed
    response_status = db.Column(db.Integer)
    response_body = db.Column(db.Text)
    
    retry_count = db.Column(db.Integer, default=0)
    last_retry_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    integration = db.relationship('Integration', backref='webhooks')
    
    def __repr__(self):
        return f'<Webhook {self.event_type}>'
