# Enterprise-Grade Features Documentation

## Overview

This document describes the enterprise-grade features implemented in TaskManager for scalability, multi-user environments, and data integrity.

## Features Implemented

### 1. 🔐 Role-Based Access Control (RBAC)

#### Built-in Roles
- **Admin**: Full system access, can manage organization and users
- **Project Manager**: Can create/manage projects and assign tasks
- **Team Member**: Can create and edit assigned tasks
- **Viewer**: Read-only access to tasks and projects

#### Granular Permissions
- **Task Permissions**: view, create, edit, delete, assign
- **Project Permissions**: view, create, edit, delete, manage members
- **Team Permissions**: view, manage
- **Organization Permissions**: manage, manage roles, view audit logs, manage integrations

#### Custom Roles
Organizations can create custom roles with specific permission combinations.

### 2. 🏢 Multi-Organization Support

#### Workspace Isolation
- Complete data isolation between organizations
- Each organization has its own users, projects, and tasks
- Automatic filtering of data by organization

#### Organization Features
- Organization settings and configuration
- Subscription tier management (free, pro, enterprise)
- User limits and feature toggles
- Data retention policies

### 3. 🔑 SSO & OAuth2 Login

#### Supported Providers
- **Google OAuth2**: Enterprise Google Workspace integration
- **Microsoft OAuth2**: Azure AD and Office 365 integration
- **Slack OAuth**: Slack workspace integration (extensible)

#### Features
- Automatic user provisioning
- Email-based user matching
- Secure token storage
- Token refresh handling

### 4. 📋 Audit Logging & Compliance

#### Audit Trail
- All user actions logged with timestamps
- IP address and user agent tracking
- Change history (old and new values)
- Success/failure status tracking

#### Data Retention
- Configurable retention periods per organization
- Automatic cleanup of old logs
- Compliance with data protection regulations

#### Audit Log Fields
- User ID and organization ID
- Action type (create, update, delete, view)
- Resource type and ID
- Request metadata (IP, user agent)
- Timestamp

### 5. 🔒 Encryption at Rest & in Transit

#### Encryption Features
- AES-256 encryption for sensitive data
- Encrypted API tokens
- Encrypted OAuth credentials
- HTTPS/TLS for all communications

#### Encrypted Fields
- API tokens
- OAuth credentials
- Sensitive configuration data
- User personal information (optional)

### 6. 🛡️ Secure API Access

#### API Token Management
- Generate secure API tokens
- Token expiration and revocation
- Scope-based permissions
- Rate limiting support

#### API Features
- RESTful endpoints with authentication
- Token-based authentication
- Request validation
- Error handling

### 7. 🔗 Integrations & Webhooks

#### Supported Integrations
- Slack notifications
- GitHub integration
- Jira integration
- Custom webhooks

#### Webhook Features
- Event-driven architecture
- Retry logic for failed deliveries
- Webhook signing for security
- Event logging

---

## API Endpoints

### Organization Management

#### List Organizations
```
GET /enterprise/organizations
Authorization: Bearer <token>

Response:
[
  {
    "id": 1,
    "name": "Acme Corp",
    "slug": "acme-corp",
    "subscription_tier": "enterprise",
    "user_count": 25
  }
]
```

#### Create Organization
```
POST /enterprise/organizations
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "New Company",
  "slug": "new-company",
  "description": "Company description",
  "subscription_tier": "pro"
}

Response: 201 Created
{
  "id": 2,
  "name": "New Company",
  "slug": "new-company"
}
```

#### Get Organization Details
```
GET /enterprise/organizations/<org_id>
Authorization: Bearer <token>

Response:
{
  "id": 1,
  "name": "Acme Corp",
  "slug": "acme-corp",
  "subscription_tier": "enterprise",
  "subscription_active": true,
  "user_count": 25,
  "max_users": 100,
  "features": {
    "sso_enabled": true,
    "api_enabled": true,
    "audit_logging_enabled": true,
    "encryption_enabled": true
  }
}
```

### Role Management

#### List Roles
```
GET /enterprise/organizations/<org_id>/roles
Authorization: Bearer <token>

Response:
[
  {
    "id": 1,
    "name": "Custom Manager",
    "description": "Custom role for managers",
    "permissions": {
      "view_tasks": true,
      "create_tasks": true,
      "edit_tasks": true,
      "delete_tasks": false
    }
  }
]
```

#### Create Custom Role
```
POST /enterprise/organizations/<org_id>/roles
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Senior Developer",
  "description": "Senior developer role",
  "permissions": {
    "view_tasks": true,
    "create_tasks": true,
    "edit_tasks": true,
    "delete_tasks": true,
    "assign_tasks": true
  }
}

Response: 201 Created
```

#### List Organization Members
```
GET /enterprise/organizations/<org_id>/members
Authorization: Bearer <token>

Response:
[
  {
    "user_id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "role": "admin",
    "joined_at": "2024-05-01T10:00:00"
  }
]
```

#### Update Member Role
```
PUT /enterprise/organizations/<org_id>/members/<user_id>
Authorization: Bearer <token>
Content-Type: application/json

{
  "role": "project_manager"
}

Response: 200 OK
```

### API Token Management

#### List API Tokens
```
GET /enterprise/organizations/<org_id>/api-tokens
Authorization: Bearer <token>

Response:
[
  {
    "id": 1,
    "name": "CI/CD Pipeline",
    "created_at": "2024-05-01T10:00:00",
    "expires_at": "2024-08-01T10:00:00",
    "last_used_at": "2024-05-15T14:30:00",
    "is_revoked": false
  }
]
```

#### Create API Token
```
POST /enterprise/organizations/<org_id>/api-tokens
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Integration Token",
  "expires_in_days": 90
}

Response: 201 Created
{
  "token": "sk_live_abc123...",
  "message": "Save this token securely. You won't be able to see it again."
}
```

#### Revoke API Token
```
DELETE /enterprise/organizations/<org_id>/api-tokens/<token_id>
Authorization: Bearer <token>

Response: 200 OK
```

### Audit Logging

#### Get Audit Logs
```
GET /enterprise/organizations/<org_id>/audit-logs?page=1&per_page=50&action=create&resource_type=task
Authorization: Bearer <token>

Response:
{
  "total": 1250,
  "pages": 25,
  "current_page": 1,
  "logs": [
    {
      "id": 1,
      "user_id": 1,
      "action": "create",
      "resource_type": "task",
      "resource_id": 42,
      "status": "success",
      "ip_address": "192.168.1.1",
      "created_at": "2024-05-15T14:30:00"
    }
  ]
}
```

### SSO & OAuth

#### Get OAuth Configuration
```
GET /enterprise/organizations/<org_id>/oauth/config
Authorization: Bearer <token>

Response:
[
  {
    "id": 1,
    "provider": "google",
    "is_enabled": true
  }
]
```

#### Create OAuth Configuration
```
POST /enterprise/organizations/<org_id>/oauth/config
Authorization: Bearer <token>
Content-Type: application/json

{
  "provider": "google",
  "client_id": "your-client-id",
  "client_secret": "your-client-secret",
  "redirect_uri": "https://taskmanager.example.com/oauth/callback/google"
}

Response: 201 Created
```

#### Initiate OAuth Flow
```
GET /oauth/authorize/google?org_id=1

Redirects to Google login
```

#### OAuth Callback
```
GET /oauth/callback/google?code=<auth_code>&state=<state>

Redirects to dashboard after successful login
```

### Integrations

#### List Integrations
```
GET /enterprise/organizations/<org_id>/integrations
Authorization: Bearer <token>

Response:
[
  {
    "id": 1,
    "name": "Slack Notifications",
    "service_type": "slack",
    "is_enabled": true
  }
]
```

#### Create Integration
```
POST /enterprise/organizations/<org_id>/integrations
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "GitHub Integration",
  "service_type": "github",
  "config": {
    "repository": "myrepo",
    "branch": "main"
  }
}

Response: 201 Created
{
  "id": 2,
  "name": "GitHub Integration",
  "webhook_secret": "whsec_abc123..."
}
```

---

## Configuration

### Environment Variables

```env
# Encryption
ENCRYPTION_KEY=your-fernet-key-here

# OAuth Providers
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret

# API
API_RATE_LIMIT=1000  # requests per hour
API_TOKEN_EXPIRY_DAYS=90

# Audit Logging
AUDIT_LOG_RETENTION_DAYS=365
AUDIT_LOG_CLEANUP_ENABLED=true

# Features
ENABLE_SSO=true
ENABLE_API_TOKENS=true
ENABLE_AUDIT_LOGGING=true
ENABLE_ENCRYPTION=true
```

### Generate Encryption Key

```bash
python -c "from enterprise import EncryptionManager; print(EncryptionManager.generate_key())"
```

---

## Usage Examples

### Python Client with API Token

```python
import requests

# Create client
class TaskManagerClient:
    def __init__(self, base_url, api_token):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def get_projects(self, org_id):
        """Get projects for organization"""
        response = requests.get(
            f"{self.base_url}/api/projects",
            headers=self.headers,
            params={"org_id": org_id}
        )
        return response.json()
    
    def create_task(self, org_id, project_id, title, description):
        """Create a new task"""
        response = requests.post(
            f"{self.base_url}/api/tasks",
            headers=self.headers,
            json={
                "org_id": org_id,
                "project_id": project_id,
                "title": title,
                "description": description
            }
        )
        return response.json()

# Usage
client = TaskManagerClient(
    "https://taskmanager.example.com",
    "sk_live_abc123..."
)

projects = client.get_projects(org_id=1)
print(projects)
```

### JavaScript Client

```javascript
class TaskManagerClient {
    constructor(baseUrl, apiToken) {
        this.baseUrl = baseUrl;
        this.apiToken = apiToken;
    }
    
    async request(method, endpoint, data = null) {
        const options = {
            method,
            headers: {
                "Authorization": `Bearer ${this.apiToken}`,
                "Content-Type": "application/json"
            }
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(
            `${this.baseUrl}${endpoint}`,
            options
        );
        
        return response.json();
    }
    
    async getProjects(orgId) {
        return this.request("GET", `/api/projects?org_id=${orgId}`);
    }
    
    async createTask(orgId, projectId, title, description) {
        return this.request("POST", "/api/tasks", {
            org_id: orgId,
            project_id: projectId,
            title,
            description
        });
    }
}

// Usage
const client = new TaskManagerClient(
    "https://taskmanager.example.com",
    "sk_live_abc123..."
);

const projects = await client.getProjects(1);
console.log(projects);
```

---

## Security Best Practices

### API Token Security
1. **Never hardcode tokens** in source code
2. **Use environment variables** for token storage
3. **Rotate tokens regularly** (every 90 days)
4. **Revoke compromised tokens** immediately
5. **Use HTTPS only** for API requests
6. **Implement rate limiting** to prevent abuse

### OAuth Security
1. **Validate state parameter** to prevent CSRF
2. **Use HTTPS redirect URIs** only
3. **Store tokens securely** (encrypted)
4. **Implement token refresh** logic
5. **Validate SSL certificates** in production

### Encryption
1. **Use strong encryption keys** (256-bit minimum)
2. **Rotate encryption keys** periodically
3. **Store keys securely** (not in code)
4. **Use HTTPS** for all communications
5. **Enable encryption at rest** for sensitive data

### Audit Logging
1. **Enable audit logging** for all organizations
2. **Monitor audit logs** for suspicious activity
3. **Retain logs** according to compliance requirements
4. **Protect audit logs** from tampering
5. **Review logs regularly** for security incidents

---

## Compliance & Data Protection

### GDPR Compliance
- User data can be exported
- Right to be forgotten (data deletion)
- Data retention policies
- Audit logging for accountability

### SOC 2 Compliance
- Encryption at rest and in transit
- Access controls and RBAC
- Audit logging and monitoring
- Regular security assessments

### HIPAA Compliance
- Encryption for protected health information
- Access controls and audit logging
- Business associate agreements
- Data breach notification procedures

---

## Troubleshooting

### OAuth Not Working
- Verify OAuth credentials are correct
- Check redirect URI matches configuration
- Ensure HTTPS is used
- Check browser console for errors

### API Token Errors
- Verify token is not expired
- Check token is not revoked
- Ensure token has required scopes
- Verify organization has API enabled

### Audit Logs Not Appearing
- Verify audit logging is enabled
- Check user has view_audit_log permission
- Ensure organization has audit logging enabled
- Check database for audit log entries

### Encryption Errors
- Verify ENCRYPTION_KEY is set
- Check encryption key is valid
- Ensure database can store encrypted data
- Review error logs for details

---

## Performance Considerations

### Database Optimization
- Index organization_id for faster queries
- Index user_id for audit logs
- Implement pagination for large result sets
- Use database connection pooling

### Caching
- Cache organization settings
- Cache role permissions
- Cache OAuth configurations
- Implement cache invalidation

### Scalability
- Use read replicas for audit logs
- Implement sharding by organization
- Use message queues for webhooks
- Implement async processing

---

## Future Enhancements

- [ ] SAML 2.0 support
- [ ] Advanced permission inheritance
- [ ] Audit log export (CSV, JSON)
- [ ] Compliance reports
- [ ] Advanced webhook filtering
- [ ] IP whitelisting
- [ ] Two-factor authentication
- [ ] Session management
- [ ] Device management
- [ ] Advanced analytics

---

**Last Updated**: May 2024
**Version**: 1.0
**Status**: Production Ready
