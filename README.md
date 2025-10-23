# Tekista

A modern Flask-based project and task management application with advanced features.

## 🚀 Features

- **User Authentication**: Secure register/login with Flask-Login
- **RBAC & Admin Tools**: Admin-only pages for reports, user management, and audit viewing
- **Project Management**: Deadlines, team assignments, and progress tracking per project
- **Task Tracking**: Priorities, dependencies, subtasks, comments, and status workflow
- **Collaboration**: Multi-assignee tasks and team views
- **File Management**: Upload/download/delete project files (with audit logs)
- **Email Notifications**: Task assignment and status-change notifications (optional mail setup)
- **Real-time**: Socket.IO integration prepared for live updates/notifications
- **REST API**: Token/session authenticated API for Projects/Tasks and analytics
- **Analytics**: Metrics, performance, activity, and project analytics endpoints
- **CSV Export**: Export project tasks to CSV
- **Modern UI**: Responsive interface with utility-first styles
- **Database**: SQLAlchemy ORM (SQLite by default; PostgreSQL/MySQL supported via URI)

## 🛠️ Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Configuration
Create a `.env` file in the project root:
```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
FLASK_APP=app.py

# Database Configuration
DATABASE_URL=sqlite:///app.db

# Mail Configuration (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# App Configuration
APP_BASE_URL=http://localhost:5000
```

### 3. Initialize Database
```bash
python init_db.py
```

This will create the database tables and optionally create sample data.

### 4. Run the Application
```bash
flask run
```

The application will be available at `http://localhost:5000`

## 📱 Usage

### Web Interface
1. Register a new account or use the sample accounts:
   - admin / admin123
   - john_doe / password123
   - jane_smith / password123

2. Create projects and assign team members
3. Add tasks with dependencies and priorities
4. Track progress and collaborate with your team

### REST API

#### Authentication
```bash
# Get API token
curl -X POST http://localhost:5000/api/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

#### API Endpoints
- `GET /api/projects` - List all projects
- `GET /api/projects/{id}` - Get project details
- `GET /api/tasks` - List all tasks
- `POST /api/tasks` - Create new task
- `GET /api/tasks/{id}` - Get task details

## 🐳 Docker Support

Build and run with Docker:
```bash
docker build -t tekista .
docker run -p 5000:5000 --env-file .env tekista
```

Using Docker Compose (recommended):
```bash
docker-compose up --build
```

## 🔧 Advanced Features

- **Task Dependencies**: Set up task dependencies to ensure proper workflow
- **Priority Management**: Assign Low, Normal, or High priorities to tasks
- **Status Tracking**: Track tasks through To Do, In Progress, and Done states
- **Email Notifications**: Get notified when tasks are assigned or status changes
- **CSV Export**: Export project tasks to CSV format
- **API Token Management**: Generate and revoke API tokens for secure access

## 📊 Database Schema

The application uses the following main entities:
- **Users**: Authentication and user management
- **Projects**: Project containers with deadlines and team assignments
- **Tasks**: Individual work items with dependencies and assignees
- **Comments**: Task discussion and collaboration
- **Associations**: Many-to-many relationships for project users and task assignees

## 🚀 Quick Start

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Initialize database: `python init_db.py`
4. Run application: `flask run`
5. Open browser to `http://localhost:5000`
6. Login with admin/admin123 to get started!

---

## 🧱 Architecture Overview

- **App Factory**: `app.create_app()` wires extensions, blueprints, error handlers
- **Blueprints**:
  - `auth/` for authentication (`/login`, `/register`, `/logout`)
  - `projects/` for project pages and CSV export
  - `tasks/` for task CRUD and details
  - `api/` for REST API (token, CRUD, analytics)
  - `notifications_*` for notification integrations
- **Models**: `models.py` with `User`, `Project`, `Task`, `Comment`, `Role`, `AuditLog`
- **Realtime**: Socket.IO setup via `socket_events.init_socketio()`

## 📁 Directory Structure

```
app.py                   # App factory and core routes
models.py                # SQLAlchemy models
auth/, projects/, tasks/ # Blueprints (routes, forms, templates)
api/                     # REST API and token auth
templates/               # Jinja HTML templates
static/                  # CSS/JS assets
tests/                   # Pytest test suite
docker-compose.yml       # Local container orchestration
```

## ⚙️ Environment Variables

See `.env.example`. Common keys:
- `SECRET_KEY` — Flask secret
- `SQLALCHEMY_DATABASE_URI` or `DATABASE_URL` — DB connection (SQLite by default)
- `MAIL_*` — optional email delivery
- `APP_BASE_URL` — base URL

## ▶️ Running

- **Dev**: `flask run` (ensure `FLASK_APP=app.py` or use `python app.py`)
- **Init DB**: `python init_db.py`
- **WS/SocketIO**: Initialized in `app.create_app()`; use `flask run` or production SocketIO server as needed
- **Docker**: `docker-compose up --build`

## ✅ Testing

Pytest-based suite located in `tests/`.

```
pytest -q
pytest --cov=. -q
```

Coverage includes auth flows, RBAC/audit, API CRUD, project filters, tasks, admin reports, analytics.

## 🌐 API Overview

- **Auth**
  - `POST /api/token` — issue API token (username/password)
  - `POST /api/token/revoke` — revoke token (requires auth)
- **Projects**
  - `GET/POST /api/projects`
  - `GET/PATCH/DELETE /api/projects/<id>`
  - `GET /projects/<id>/export` — CSV export (admin only)
- **Tasks**
  - `GET/POST /api/tasks`
  - `GET/PATCH/DELETE /api/tasks/<id>`
- **Analytics**
  - `GET /api/analytics/metrics`
  - `GET /api/analytics/performance`
  - `GET /api/activity`
  - `GET /api/projects/<id>/analytics`

## 🔒 Admin Tools

- `GET /reports` — admin reports page (RBAC protected)
- `GET/POST /admin/users` — user role management and filters
- `GET /admin/audit` — audit log viewer with filters
- File operations (admin): `/files/upload`, `/files/download/...`, `/files/delete`

## 🗺️ Roadmap / Future Plans

- **Enhanced Realtime**: live updates for tasks/projects over WebSocket
- **Role/Permission Editor**: UI to manage custom roles and permissions
- **Advanced Analytics**: backlog aging, burnup/burndown, velocity
- **Integrations**: GitHub/Jira import, Slack/Teams notifications
- **Attachments**: Virus scan and storage backends (S3, GCS)
- **i18n**: Multi-language support
- **E2E Tests**: Playwright/Cypress flows for critical paths

## 🤝 Contributing

Issues and PRs are welcome. Please run the test suite before submitting changes:

```
pytest -q
```

## 📄 License

MIT (or your preferred license)