# Enterprise Features Setup Guide

## Quick Start

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Generate Encryption Key

```bash
python -c "from enterprise import EncryptionManager; print(EncryptionManager.generate_key())"
```

Copy the output and add to `.env`:

```env
ENCRYPTION_KEY=your-generated-key-here
```

### Step 3: Configure Environment

Create or update `.env` file:

```env
# Flask
FLASK_ENV=production
DEBUG=false
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql://user:password@localhost/taskmanager

# Encryption
ENCRYPTION_KEY=your-encryption-key

# OAuth Providers
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=https://taskmanager.example.com/oauth/callback/google

MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
MICROSOFT_REDIRECT_URI=https://taskmanager.example.com/oauth/callback/microsoft

# Enterprise Features
ENABLE_SSO=true
ENABLE_API_TOKENS=true
ENABLE_AUDIT_LOGGING=true
ENABLE_ENCRYPTION=true

# API Configuration
API_RATE_LIMIT=1000
API_TOKEN_EXPIRY_DAYS=90

# Audit Logging
AUDIT_LOG_RETENTION_DAYS=365
AUDIT_LOG_CLEANUP_ENABLED=true
```

### Step 4: Update Database Models

Update `models.py` to include enterprise models:

```python
# Add to models.py
from enterprise.models import (
    Organization, APIToken, AuditLog, OAuthConfig, OAuthAccount,
    UserOrganizationRole, CustomRole, Integration, Webhook
)

# Update User model to include organization_id
class User(UserMixin, db.Model):
    # ... existing fields ...
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    role = db.Column(db.String(50), default='team_member')
    
    # Add methods for permission checking
    def has_permission(self, permission):
        """Check if user has specific permission"""
        from enterprise import ROLE_PERMISSIONS, Role
        
        role = Role[self.role.upper()]
        return permission in ROLE_PERMISSIONS.get(role, [])
    
    def has_organization_access(self, org_id):
        """Check if user has access to organization"""
        return self.organization_id == org_id
```

### Step 5: Register Enterprise Blueprint

Update `app.py`:

```python
from enterprise.routes import enterprise_bp

# Register blueprint
app.register_blueprint(enterprise_bp)
```

### Step 6: Initialize Database

```bash
flask db init
flask db migrate
flask db upgrade
```

### Step 7: Create Initial Organization

```bash
python -c "
from app import create_app, db
from enterprise.models import Organization

app = create_app()
with app.app_context():
    org = Organization(
        name='Default Organization',
        slug='default-org',
        subscription_tier='enterprise'
    )
    db.session.add(org)
    db.session.commit()
    print(f'Organization created: {org.id}')
"
```

### Step 8: Start Application

```bash
flask run
```

---

## OAuth Setup

### Google OAuth

1. **Create Google Cloud Project**
   - Visit https://console.cloud.google.com
   - Create new project
   - Enable Google+ API

2. **Create OAuth Credentials**
   - Go to Credentials
   - Click "Create Credentials" → "OAuth client ID"
   - Choose "Web application"
   - Add authorized redirect URIs:
     - `https://taskmanager.example.com/oauth/callback/google`
   - Copy Client ID and Client Secret

3. **Configure in TaskManager**
   - Add to `.env`:
     ```env
     GOOGLE_CLIENT_ID=your-client-id
     GOOGLE_CLIENT_SECRET=your-client-secret
     ```
   - Or configure via admin panel

### Microsoft OAuth

1. **Register Application**
   - Visit https://portal.azure.com
   - Go to Azure AD → App registrations
   - Click "New registration"
   - Enter application name

2. **Configure Redirect URI**
   - Go to Authentication
   - Add redirect URI: `https://taskmanager.example.com/oauth/callback/microsoft`

3. **Create Client Secret**
   - Go to Certificates & secrets
   - Click "New client secret"
   - Copy the secret value

4. **Configure in TaskManager**
   - Add to `.env`:
     ```env
     MICROSOFT_CLIENT_ID=your-client-id
     MICROSOFT_CLIENT_SECRET=your-client-secret
     ```

---

## API Token Management

### Generate API Token

```bash
curl -X POST https://taskmanager.example.com/enterprise/organizations/1/api-tokens \
  -H "Authorization: Bearer <user-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CI/CD Pipeline",
    "expires_in_days": 90
  }'
```

### Use API Token

```bash
curl https://taskmanager.example.com/api/projects \
  -H "Authorization: Bearer sk_live_abc123..."
```

### Revoke API Token

```bash
curl -X DELETE https://taskmanager.example.com/enterprise/organizations/1/api-tokens/1 \
  -H "Authorization: Bearer <user-token>"
```

---

## Role Management

### Create Custom Role

```bash
curl -X POST https://taskmanager.example.com/enterprise/organizations/1/roles \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Senior Developer",
    "description": "Senior developer role",
    "permissions": {
      "view_tasks": true,
      "create_tasks": true,
      "edit_tasks": true,
      "delete_tasks": true,
      "assign_tasks": true,
      "view_projects": true,
      "create_projects": true,
      "edit_projects": true
    }
  }'
```

### Assign Role to User

```bash
curl -X PUT https://taskmanager.example.com/enterprise/organizations/1/members/2 \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "project_manager"
  }'
```

---

## Audit Logging

### View Audit Logs

```bash
curl https://taskmanager.example.com/enterprise/organizations/1/audit-logs \
  -H "Authorization: Bearer <admin-token>"
```

### Filter Audit Logs

```bash
# By action
curl "https://taskmanager.example.com/enterprise/organizations/1/audit-logs?action=create" \
  -H "Authorization: Bearer <admin-token>"

# By resource type
curl "https://taskmanager.example.com/enterprise/organizations/1/audit-logs?resource_type=task" \
  -H "Authorization: Bearer <admin-token>"

# By user
curl "https://taskmanager.example.com/enterprise/organizations/1/audit-logs?user_id=1" \
  -H "Authorization: Bearer <admin-token>"
```

### Export Audit Logs

```python
from enterprise.models import AuditLog
import csv

# Query logs
logs = AuditLog.query.filter_by(organization_id=1).all()

# Export to CSV
with open('audit_logs.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['ID', 'User', 'Action', 'Resource', 'Status', 'Timestamp'])
    for log in logs:
        writer.writerow([
            log.id,
            log.user.username if log.user else 'System',
            log.action,
            f"{log.resource_type}:{log.resource_id}",
            log.status,
            log.created_at
        ])
```

---

## Integrations

### Create Slack Integration

```bash
curl -X POST https://taskmanager.example.com/enterprise/organizations/1/integrations \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Slack Notifications",
    "service_type": "slack",
    "config": {
      "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
      "channel": "#notifications",
      "events": ["task_created", "task_completed"]
    }
  }'
```

### Create GitHub Integration

```bash
curl -X POST https://taskmanager.example.com/enterprise/organizations/1/integrations \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "GitHub Integration",
    "service_type": "github",
    "config": {
      "repository": "myorg/myrepo",
      "branch": "main",
      "token": "ghp_..."
    }
  }'
```

---

## Security Hardening

### Enable HTTPS

```nginx
# Nginx configuration
server {
    listen 443 ssl http2;
    server_name taskmanager.example.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Rate Limiting

```python
# In app.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per hour"]
)

# Apply to enterprise routes
@enterprise_bp.route('/api/tokens', methods=['POST'])
@limiter.limit("10 per hour")
def create_api_token():
    pass
```

### IP Whitelisting

```python
# In app.py
ALLOWED_IPS = [
    "192.168.1.0/24",
    "10.0.0.0/8"
]

@app.before_request
def check_ip():
    from ipaddress import ip_address, ip_network
    
    client_ip = request.remote_addr
    
    for allowed_ip in ALLOWED_IPS:
        if ip_address(client_ip) in ip_network(allowed_ip):
            return
    
    return jsonify({"error": "Access denied"}), 403
```

---

## Monitoring & Maintenance

### Monitor Audit Logs

```bash
# Check for suspicious activity
curl "https://taskmanager.example.com/enterprise/organizations/1/audit-logs?status=failure" \
  -H "Authorization: Bearer <admin-token>"
```

### Cleanup Old Data

```python
from enterprise import DataRetentionPolicy

# Manual cleanup
DataRetentionPolicy.cleanup_old_data(org_id=1)

# Schedule automatic cleanup
DataRetentionPolicy.schedule_cleanup()
```

### Monitor API Usage

```python
from enterprise.models import APIToken

# Get most used tokens
tokens = APIToken.query.order_by(APIToken.last_used_at.desc()).limit(10).all()

for token in tokens:
    print(f"{token.name}: Last used {token.last_used_at}")
```

---

## Troubleshooting

### OAuth Not Working

**Problem**: OAuth login fails with "Invalid redirect URI"

**Solution**:
1. Verify redirect URI matches exactly in OAuth provider settings
2. Ensure HTTPS is used in production
3. Check OAuth credentials are correct
4. Review error logs for details

### API Token Errors

**Problem**: API token returns 401 Unauthorized

**Solution**:
1. Verify token is not expired
2. Check token is not revoked
3. Ensure token has required scopes
4. Verify organization has API enabled

### Encryption Errors

**Problem**: "Encryption key not configured"

**Solution**:
1. Generate encryption key: `python -c "from enterprise import EncryptionManager; print(EncryptionManager.generate_key())"`
2. Add to `.env`: `ENCRYPTION_KEY=<key>`
3. Restart application

### Audit Logs Not Appearing

**Problem**: Audit logs are empty

**Solution**:
1. Verify audit logging is enabled: `ENABLE_AUDIT_LOGGING=true`
2. Check user has `view_audit_log` permission
3. Verify organization has audit logging enabled
4. Check database for audit log entries

---

## Performance Tuning

### Database Optimization

```sql
-- Create indexes for faster queries
CREATE INDEX idx_audit_log_org_id ON audit_log(organization_id);
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);
CREATE INDEX idx_api_token_user_id ON api_token(user_id);
CREATE INDEX idx_user_org_role_org_id ON user_organization_role(organization_id);
```

### Connection Pooling

```python
# In app.py
from sqlalchemy.pool import QueuePool

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'poolclass': QueuePool,
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
}
```

### Caching

```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis'})

@enterprise_bp.route('/organizations/<int:org_id>')
@cache.cached(timeout=300)
def get_organization(org_id):
    pass
```

---

## Production Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV FLASK_APP=app.py
ENV FLASK_ENV=production

EXPOSE 5000

CMD ["gunicorn", "--workers=4", "--threads=2", "--worker-class=gthread", "app:app"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/taskmanager
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - FLASK_ENV=production
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=taskmanager
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

---

**Last Updated**: May 2024
**Version**: 1.0
**Status**: Production Ready
