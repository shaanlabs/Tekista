# TaskManager

A modern Flask-based project and task management application with advanced features.

## 🚀 Features

- **User Authentication**: Secure login/register system with Flask-Login
- **Project Management**: Create projects with deadlines and team assignments
- **Task Tracking**: Advanced task management with priorities, dependencies, and status tracking
- **Team Collaboration**: Assign tasks to multiple users and track progress
- **Email Notifications**: Automated notifications for task assignments and status changes
- **REST API**: Full REST API with token-based authentication
- **Modern UI**: Bootstrap-based responsive interface
- **Database Management**: SQLAlchemy ORM with SQLite/PostgreSQL support

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
docker build -t taskmanager .
docker run -p 5000:5000 taskmanager
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