"""
Enterprise Routes for RBAC, SSO, API tokens, and audit logging
"""

from flask import Blueprint, request, jsonify, redirect, url_for, session
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models import db, User
from enterprise import (
    require_permission, require_role, audit_log,
    APITokenManager, EncryptionManager, OAuthProvider,
    GoogleOAuthProvider, MicrosoftOAuthProvider
)
from enterprise.models import (
    Organization, APIToken, AuditLog, OAuthConfig, OAuthAccount,
    UserOrganizationRole, CustomRole, Integration, Webhook
)
import logging
import secrets

logger = logging.getLogger(__name__)

enterprise_bp = Blueprint('enterprise', __name__, url_prefix='/enterprise')

# ============================================================================
# ORGANIZATION MANAGEMENT
# ============================================================================

@enterprise_bp.route('/organizations', methods=['GET'])
@login_required
def list_organizations():
    """List organizations for current user"""
    organizations = current_user.organizations
    return jsonify([{
        'id': org.id,
        'name': org.name,
        'slug': org.slug,
        'subscription_tier': org.subscription_tier,
        'user_count': org.get_user_count()
    } for org in organizations])

@enterprise_bp.route('/organizations', methods=['POST'])
@login_required
def create_organization():
    """Create new organization"""
    data = request.get_json()
    
    # Validate input
    if not data.get('name') or not data.get('slug'):
        return jsonify({'error': 'Name and slug required'}), 400
    
    # Check if slug is unique
    if Organization.query.filter_by(slug=data['slug']).first():
        return jsonify({'error': 'Slug already exists'}), 400
    
    # Create organization
    org = Organization(
        name=data['name'],
        slug=data['slug'],
        description=data.get('description'),
        subscription_tier=data.get('subscription_tier', 'free')
    )
    
    db.session.add(org)
    db.session.commit()
    
    # Add current user as admin
    user_org_role = UserOrganizationRole(
        user_id=current_user.id,
        organization_id=org.id,
        role='admin'
    )
    db.session.add(user_org_role)
    db.session.commit()
    
    # Audit log
    AuditLog.log_action(
        current_user.id, org.id, 'create', 'organization', org.id,
        new_values={'name': org.name, 'slug': org.slug}
    )
    
    return jsonify({
        'id': org.id,
        'name': org.name,
        'slug': org.slug
    }), 201

@enterprise_bp.route('/organizations/<int:org_id>', methods=['GET'])
@login_required
@require_permission('view_organization')
def get_organization(org_id):
    """Get organization details"""
    org = Organization.query.get_or_404(org_id)
    
    # Check access
    if not current_user.has_organization_access(org_id):
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({
        'id': org.id,
        'name': org.name,
        'slug': org.slug,
        'description': org.description,
        'subscription_tier': org.subscription_tier,
        'subscription_active': org.is_subscription_active(),
        'user_count': org.get_user_count(),
        'max_users': org.max_users,
        'features': {
            'sso_enabled': org.sso_enabled,
            'api_enabled': org.api_enabled,
            'audit_logging_enabled': org.audit_logging_enabled,
            'encryption_enabled': org.encryption_enabled
        }
    })

# ============================================================================
# ROLE-BASED ACCESS CONTROL
# ============================================================================

@enterprise_bp.route('/organizations/<int:org_id>/roles', methods=['GET'])
@login_required
@require_role('admin', 'project_manager')
def list_roles(org_id):
    """List roles in organization"""
    org = Organization.query.get_or_404(org_id)
    
    if not current_user.has_organization_access(org_id):
        return jsonify({'error': 'Unauthorized'}), 403
    
    custom_roles = CustomRole.query.filter_by(organization_id=org_id).all()
    
    return jsonify([{
        'id': role.id,
        'name': role.name,
        'description': role.description,
        'permissions': role.permissions
    } for role in custom_roles])

@enterprise_bp.route('/organizations/<int:org_id>/roles', methods=['POST'])
@login_required
@require_role('admin')
def create_role(org_id):
    """Create custom role"""
    org = Organization.query.get_or_404(org_id)
    
    if not current_user.has_organization_access(org_id):
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    role = CustomRole(
        organization_id=org_id,
        name=data.get('name'),
        description=data.get('description'),
        permissions=data.get('permissions', {})
    )
    
    db.session.add(role)
    db.session.commit()
    
    # Audit log
    AuditLog.log_action(
        current_user.id, org_id, 'create', 'role', role.id,
        new_values={'name': role.name}
    )
    
    return jsonify({
        'id': role.id,
        'name': role.name,
        'permissions': role.permissions
    }), 201

@enterprise_bp.route('/organizations/<int:org_id>/members', methods=['GET'])
@login_required
def list_members(org_id):
    """List organization members"""
    org = Organization.query.get_or_404(org_id)
    
    if not current_user.has_organization_access(org_id):
        return jsonify({'error': 'Unauthorized'}), 403
    
    members = UserOrganizationRole.query.filter_by(organization_id=org_id).all()
    
    return jsonify([{
        'user_id': member.user_id,
        'username': member.user.username,
        'email': member.user.email,
        'role': member.role,
        'joined_at': member.created_at.isoformat()
    } for member in members])

@enterprise_bp.route('/organizations/<int:org_id>/members/<int:user_id>', methods=['PUT'])
@login_required
@require_role('admin')
def update_member_role(org_id, user_id):
    """Update member role"""
    org = Organization.query.get_or_404(org_id)
    
    if not current_user.has_organization_access(org_id):
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    member = UserOrganizationRole.query.filter_by(
        organization_id=org_id,
        user_id=user_id
    ).first_or_404()
    
    old_role = member.role
    member.role = data.get('role')
    db.session.commit()
    
    # Audit log
    AuditLog.log_action(
        current_user.id, org_id, 'update', 'user_role', user_id,
        old_values={'role': old_role},
        new_values={'role': member.role}
    )
    
    return jsonify({'success': True})

# ============================================================================
# API TOKEN MANAGEMENT
# ============================================================================

@enterprise_bp.route('/organizations/<int:org_id>/api-tokens', methods=['GET'])
@login_required
def list_api_tokens(org_id):
    """List API tokens for organization"""
    org = Organization.query.get_or_404(org_id)
    
    if not current_user.has_organization_access(org_id):
        return jsonify({'error': 'Unauthorized'}), 403
    
    tokens = APIToken.query.filter_by(
        organization_id=org_id,
        user_id=current_user.id
    ).all()
    
    return jsonify([{
        'id': token.id,
        'name': token.name,
        'created_at': token.created_at.isoformat(),
        'expires_at': token.expires_at.isoformat(),
        'last_used_at': token.last_used_at.isoformat() if token.last_used_at else None,
        'is_revoked': token.is_revoked
    } for token in tokens])

@enterprise_bp.route('/organizations/<int:org_id>/api-tokens', methods=['POST'])
@login_required
def create_api_token(org_id):
    """Create new API token"""
    org = Organization.query.get_or_404(org_id)
    
    if not org.api_enabled:
        return jsonify({'error': 'API not enabled for this organization'}), 403
    
    if not current_user.has_organization_access(org_id):
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    token = APITokenManager.generate_token(
        current_user.id,
        org_id,
        data.get('name', 'API Token'),
        data.get('expires_in_days', 90)
    )
    
    # Audit log
    AuditLog.log_action(
        current_user.id, org_id, 'create', 'api_token', None,
        new_values={'name': data.get('name')}
    )
    
    return jsonify({
        'token': token,
        'message': 'Save this token securely. You won\'t be able to see it again.'
    }), 201

@enterprise_bp.route('/organizations/<int:org_id>/api-tokens/<int:token_id>', methods=['DELETE'])
@login_required
def revoke_api_token(org_id, token_id):
    """Revoke API token"""
    org = Organization.query.get_or_404(org_id)
    
    if not current_user.has_organization_access(org_id):
        return jsonify({'error': 'Unauthorized'}), 403
    
    token = APIToken.query.get_or_404(token_id)
    
    if token.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    APITokenManager.revoke_token(token_id)
    
    # Audit log
    AuditLog.log_action(
        current_user.id, org_id, 'delete', 'api_token', token_id,
        new_values={'is_revoked': True}
    )
    
    return jsonify({'success': True})

# ============================================================================
# AUDIT LOGGING
# ============================================================================

@enterprise_bp.route('/organizations/<int:org_id>/audit-logs', methods=['GET'])
@login_required
@require_permission('view_audit_log')
def get_audit_logs(org_id):
    """Get audit logs for organization"""
    org = Organization.query.get_or_404(org_id)
    
    if not current_user.has_organization_access(org_id):
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    # Filters
    action = request.args.get('action')
    resource_type = request.args.get('resource_type')
    user_id = request.args.get('user_id', type=int)
    
    query = AuditLog.query.filter_by(organization_id=org_id)
    
    if action:
        query = query.filter_by(action=action)
    if resource_type:
        query = query.filter_by(resource_type=resource_type)
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    logs = query.order_by(AuditLog.created_at.desc()).paginate(
        page=page,
        per_page=per_page
    )
    
    return jsonify({
        'total': logs.total,
        'pages': logs.pages,
        'current_page': page,
        'logs': [{
            'id': log.id,
            'user_id': log.user_id,
            'action': log.action,
            'resource_type': log.resource_type,
            'resource_id': log.resource_id,
            'status': log.status,
            'ip_address': log.ip_address,
            'created_at': log.created_at.isoformat()
        } for log in logs.items]
    })

# ============================================================================
# SSO & OAUTH
# ============================================================================

@enterprise_bp.route('/organizations/<int:org_id>/oauth/config', methods=['GET'])
@login_required
@require_role('admin')
def get_oauth_config(org_id):
    """Get OAuth configuration"""
    org = Organization.query.get_or_404(org_id)
    
    if not current_user.has_organization_access(org_id):
        return jsonify({'error': 'Unauthorized'}), 403
    
    configs = OAuthConfig.query.filter_by(organization_id=org_id).all()
    
    return jsonify([{
        'id': config.id,
        'provider': config.provider,
        'is_enabled': config.is_enabled
    } for config in configs])

@enterprise_bp.route('/organizations/<int:org_id>/oauth/config', methods=['POST'])
@login_required
@require_role('admin')
def create_oauth_config(org_id):
    """Create OAuth configuration"""
    org = Organization.query.get_or_404(org_id)
    
    if not current_user.has_organization_access(org_id):
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Check if config already exists
    existing = OAuthConfig.query.filter_by(
        organization_id=org_id,
        provider=data.get('provider')
    ).first()
    
    if existing:
        return jsonify({'error': 'OAuth config already exists for this provider'}), 400
    
    # Encrypt client secret
    encryption_manager = EncryptionManager()
    encrypted_secret = encryption_manager.encrypt(data.get('client_secret'))
    
    config = OAuthConfig(
        organization_id=org_id,
        provider=data.get('provider'),
        client_id=data.get('client_id'),
        client_secret=encrypted_secret,
        redirect_uri=data.get('redirect_uri'),
        is_enabled=True
    )
    
    db.session.add(config)
    db.session.commit()
    
    # Audit log
    AuditLog.log_action(
        current_user.id, org_id, 'create', 'oauth_config', config.id,
        new_values={'provider': config.provider}
    )
    
    return jsonify({
        'id': config.id,
        'provider': config.provider
    }), 201

@enterprise_bp.route('/oauth/authorize/<provider>', methods=['GET'])
def oauth_authorize(provider):
    """Initiate OAuth flow"""
    org_id = request.args.get('org_id', type=int)
    
    if not org_id:
        return jsonify({'error': 'Organization ID required'}), 400
    
    org = Organization.query.get_or_404(org_id)
    
    # Get OAuth config
    config = OAuthConfig.query.filter_by(
        organization_id=org_id,
        provider=provider,
        is_enabled=True
    ).first_or_404()
    
    # Decrypt client secret
    encryption_manager = EncryptionManager()
    client_secret = encryption_manager.decrypt(config.client_secret)
    
    # Create OAuth provider
    if provider == 'google':
        oauth_provider = GoogleOAuthProvider(
            config.client_id,
            client_secret,
            config.redirect_uri
        )
    elif provider == 'microsoft':
        oauth_provider = MicrosoftOAuthProvider(
            config.client_id,
            client_secret,
            config.redirect_uri
        )
    else:
        return jsonify({'error': 'Unsupported provider'}), 400
    
    # Generate state
    state = secrets.token_urlsafe(32)
    session[f'oauth_state_{provider}'] = state
    session[f'oauth_org_id_{provider}'] = org_id
    
    # Get authorization URL
    auth_url = oauth_provider.get_authorization_url(state)
    
    return redirect(auth_url)

@enterprise_bp.route('/oauth/callback/<provider>', methods=['GET'])
def oauth_callback(provider):
    """OAuth callback handler"""
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code or not state:
        return jsonify({'error': 'Missing code or state'}), 400
    
    # Verify state
    stored_state = session.get(f'oauth_state_{provider}')
    if not stored_state or stored_state != state:
        return jsonify({'error': 'Invalid state'}), 400
    
    org_id = session.get(f'oauth_org_id_{provider}')
    
    # Get OAuth config
    config = OAuthConfig.query.filter_by(
        organization_id=org_id,
        provider=provider
    ).first_or_404()
    
    # Decrypt client secret
    encryption_manager = EncryptionManager()
    client_secret = encryption_manager.decrypt(config.client_secret)
    
    # Create OAuth provider
    if provider == 'google':
        oauth_provider = GoogleOAuthProvider(
            config.client_id,
            client_secret,
            config.redirect_uri
        )
    elif provider == 'microsoft':
        oauth_provider = MicrosoftOAuthProvider(
            config.client_id,
            client_secret,
            config.redirect_uri
        )
    else:
        return jsonify({'error': 'Unsupported provider'}), 400
    
    # Exchange code for token
    token_response = oauth_provider.exchange_code_for_token(code)
    access_token = token_response.get('access_token')
    
    # Get user info
    user_info = oauth_provider.get_user_info(access_token)
    
    # Find or create user
    oauth_account = OAuthAccount.query.filter_by(
        provider=provider,
        provider_user_id=user_info.get('id') or user_info.get('sub')
    ).first()
    
    if oauth_account:
        user = oauth_account.user
    else:
        # Create new user
        user = User(
            username=user_info.get('email', '').split('@')[0],
            email=user_info.get('email'),
            organization_id=org_id
        )
        db.session.add(user)
        db.session.commit()
        
        # Create OAuth account
        oauth_account = OAuthAccount(
            user_id=user.id,
            provider=provider,
            provider_user_id=user_info.get('id') or user_info.get('sub'),
            provider_email=user_info.get('email'),
            access_token=access_token,
            refresh_token=token_response.get('refresh_token'),
            token_expires_at=datetime.utcnow() + timedelta(seconds=token_response.get('expires_in', 3600))
        )
        db.session.add(oauth_account)
        db.session.commit()
        
        # Add user to organization
        user_org_role = UserOrganizationRole(
            user_id=user.id,
            organization_id=org_id,
            role='team_member'
        )
        db.session.add(user_org_role)
        db.session.commit()
    
    # Log user in
    from flask_login import login_user
    login_user(user)
    
    # Audit log
    AuditLog.log_action(
        user.id, org_id, 'login', 'user', user.id,
        details={'provider': provider}
    )
    
    return redirect(url_for('projects.list_projects'))

# ============================================================================
# INTEGRATIONS & WEBHOOKS
# ============================================================================

@enterprise_bp.route('/organizations/<int:org_id>/integrations', methods=['GET'])
@login_required
@require_permission('manage_integrations')
def list_integrations(org_id):
    """List integrations"""
    org = Organization.query.get_or_404(org_id)
    
    if not current_user.has_organization_access(org_id):
        return jsonify({'error': 'Unauthorized'}), 403
    
    integrations = Integration.query.filter_by(organization_id=org_id).all()
    
    return jsonify([{
        'id': integration.id,
        'name': integration.name,
        'service_type': integration.service_type,
        'is_enabled': integration.is_enabled
    } for integration in integrations])

@enterprise_bp.route('/organizations/<int:org_id>/integrations', methods=['POST'])
@login_required
@require_permission('manage_integrations')
def create_integration(org_id):
    """Create integration"""
    org = Organization.query.get_or_404(org_id)
    
    if not current_user.has_organization_access(org_id):
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    integration = Integration(
        organization_id=org_id,
        name=data.get('name'),
        service_type=data.get('service_type'),
        config=data.get('config', {}),
        webhook_secret=secrets.token_urlsafe(32)
    )
    
    db.session.add(integration)
    db.session.commit()
    
    # Audit log
    AuditLog.log_action(
        current_user.id, org_id, 'create', 'integration', integration.id,
        new_values={'name': integration.name, 'service_type': integration.service_type}
    )
    
    return jsonify({
        'id': integration.id,
        'name': integration.name,
        'webhook_secret': integration.webhook_secret
    }), 201
