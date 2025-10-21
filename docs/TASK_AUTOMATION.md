# Task Automation & Performance Tracking System

## Overview

An intelligent automation system that automatically assigns new tasks to users upon completion, recalculates performance metrics, and maintains optimal workload balance using Celery background jobs.

---

## 🎯 Features

### 1. Automatic Task Assignment
- ✅ Triggers when user completes a task
- ✅ Finds next best task using skill matching
- ✅ Considers user workload and capacity
- ✅ Non-blocking background processing

### 2. Performance Metrics
- ✅ Calculates performance score on task completion
- ✅ Tracks estimation accuracy
- ✅ Monitors on-time completion
- ✅ Measures skill utilization

### 3. Workload Management
- ✅ Tracks current workload hours
- ✅ Prevents overloading
- ✅ Suggests rebalancing
- ✅ Monitors team capacity

### 4. Notifications
- ✅ In-app task assignment alerts
- ✅ Performance update notifications
- ✅ Workload warnings
- ✅ Real-time status updates

### 5. Scheduled Jobs
- ✅ Daily performance reports
- ✅ Hourly task assignment
- ✅ Automatic cleanup
- ✅ Team rebalancing

---

## 🏗️ Architecture

### Components

#### 1. Celery App (`celery_app.py`)
- Background job queue
- Task definitions
- Scheduled jobs (Celery Beat)
- Retry logic with exponential backoff

#### 2. Automation Engine (`automation/__init__.py`)
- Task completion handler
- Performance calculator
- Workload balancer
- Automation triggers

#### 3. API Routes (`automation/routes.py`)
- Task completion endpoints
- Performance tracking endpoints
- Workload management endpoints
- Job status monitoring

---

## 📊 Workflow

### Task Completion Flow

```
1. User completes task
   ↓
2. Mark task as Done
   ↓
3. Trigger automation (non-blocking)
   ├─ Update performance metrics
   ├─ Find next best task
   ├─ Assign new task
   └─ Send notifications
   ↓
4. Return response to user immediately
```

### Performance Calculation

```
Performance Score = (
    35% × Completion Rate +
    25% × Estimation Accuracy +
    20% × Workload Balance +
    20% × Skill Utilization
) × 100
```

---

## 🔧 Configuration

### Environment Variables

```env
# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Task Configuration
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=['json']
CELERY_TIMEZONE=UTC

# Retry Configuration
CELERY_TASK_MAX_RETRIES=3
CELERY_TASK_DEFAULT_RETRY_DELAY=60
```

### Redis Setup

```bash
# Install Redis
brew install redis  # macOS
sudo apt-get install redis-server  # Ubuntu

# Start Redis
redis-server

# Or with Docker
docker run -d -p 6379:6379 redis:latest
```

---

## 📡 API Endpoints

### Task Completion

#### Complete Task
```
POST /automation/tasks/<task_id>/complete
Authorization: Bearer <token>
Content-Type: application/json

{
    "actual_hours": 5.5,
    "notes": "Completed ahead of schedule"
}

Response: 200 OK
{
    "success": true,
    "message": "Task completed",
    "automation": {
        "success": true,
        "task_id": 42,
        "user_id": 5,
        "jobs": {
            "performance_update": "job-id-1",
            "next_task_assignment": "job-id-2"
        }
    }
}
```

#### Update Task Status
```
PUT /automation/tasks/<task_id>/status
Authorization: Bearer <token>
Content-Type: application/json

{
    "status": "Done"
}

Response: 200 OK
```

### Performance Tracking

#### Get User Performance
```
GET /automation/performance/user/<user_id>
Authorization: Bearer <token>

Response: 200 OK
{
    "user_id": 5,
    "performance_score": 87.5,
    "completion_rate": 92.3,
    "estimation_accuracy": 85.0,
    "workload_balance": 78.5,
    "skill_utilization": 90.0,
    "total_assignments": 42,
    "completed_assignments": 38
}
```

#### Get Team Performance
```
GET /automation/performance/team
Authorization: Bearer <token>

Response: 200 OK
{
    "organization_id": 1,
    "average_performance": 82.3,
    "team_members": [
        {
            "user_id": 5,
            "username": "john_doe",
            "performance_score": 87.5,
            ...
        }
    ]
}
```

#### Get High Performers
```
GET /automation/performance/high-performers?threshold=80
Authorization: Bearer <token>

Response: 200 OK
{
    "threshold": 80,
    "count": 5,
    "high_performers": [...]
}
```

#### Get At-Risk Performers
```
GET /automation/performance/at-risk?threshold=50
Authorization: Bearer <token>

Response: 200 OK
{
    "threshold": 50,
    "count": 2,
    "at_risk_performers": [...]
}
```

### Workload Management

#### Get User Capacity
```
GET /automation/workload/user/<user_id>/capacity
Authorization: Bearer <token>

Response: 200 OK
{
    "user_id": 5,
    "available_capacity_hours": 12.0,
    "is_overloaded": false
}
```

#### Get Rebalance Suggestions
```
GET /automation/workload/team/rebalance-suggestions
Authorization: Bearer <token>

Response: 200 OK
{
    "overloaded_users": [
        {
            "user_id": 3,
            "username": "jane_smith",
            "utilization": 95.0,
            "current_hours": 38.0,
            "max_hours": 40.0
        }
    ],
    "underutilized_users": [
        {
            "user_id": 7,
            "username": "bob_jones",
            "utilization": 30.0,
            "available_capacity": 28.0
        }
    ],
    "rebalancing_needed": true
}
```

#### Get Team Workload Status
```
GET /automation/workload/team/status
Authorization: Bearer <token>

Response: 200 OK
{
    "total_team_members": 8,
    "total_capacity_hours": 320.0,
    "total_utilized_hours": 285.0,
    "utilization_rate": 89.1,
    "overloaded_members": 2,
    "available_capacity": 35.0
}
```

### Job Monitoring

#### Get Job Status
```
GET /automation/jobs/<job_id>/status
Authorization: Bearer <token>

Response: 200 OK
{
    "job_id": "abc123def456",
    "status": "SUCCESS",
    "result": {
        "success": true,
        "task_id": 42
    }
}
```

#### Get Automation Log
```
GET /automation/automation-log?page=1&per_page=50
Authorization: Bearer <token>

Response: 200 OK
{
    "total": 150,
    "pages": 3,
    "current_page": 1,
    "logs": [
        {
            "id": 1,
            "user": "john_doe",
            "action": "complete",
            "resource_type": "task",
            "resource_id": 42,
            "status": "success",
            "created_at": "2024-05-15T14:30:00"
        }
    ]
}
```

---

## 🔄 Background Jobs

### Task Assignment Job

```python
@celery_app.task(bind=True, max_retries=3)
def assign_next_task_for_user(self, user_id):
    """
    Automatically assign next best task to user
    
    Retries up to 3 times with exponential backoff
    """
    # Finds best matching task
    # Assigns to user
    # Sends notification
```

### Performance Update Job

```python
@celery_app.task(bind=True, max_retries=3)
def update_user_performance_metrics(self, user_id, assignment_id):
    """
    Update performance score after task completion
    
    Calculates:
    - Estimation accuracy
    - On-time completion
    - Skill match
    - Overall performance
    """
```

### Scheduled Jobs

| Job | Schedule | Purpose |
|-----|----------|---------|
| Cleanup Old Assignments | Daily 2 AM | Remove completed assignments older than 90 days |
| Generate Daily Reports | Daily 8 AM | Calculate team performance metrics |
| Find & Assign Tasks | Every hour | Assign tasks to available users |

---

## 📈 Performance Metrics

### Components

- **Completion Rate** (35%): Percentage of assigned tasks completed
- **Estimation Accuracy** (25%): How close estimates are to actual time
- **Workload Balance** (20%): Ratio of used capacity to maximum
- **Skill Utilization** (20%): How well tasks match user skills

### Calculation Example

```
User Stats:
- Completed: 38/42 tasks (90.5%)
- Estimation Accuracy: 85%
- Workload: 28/40 hours (70%)
- Skill Match: 90%

Performance Score = (
    0.35 × 90.5 +
    0.25 × 85 +
    0.20 × 70 +
    0.20 × 90
) × 100 = 84.7
```

---

## 🚀 Usage Examples

### Python Integration

```python
from automation import TaskAutomationEngine, PerformanceCalculator

# Handle task completion
result = TaskAutomationEngine.on_task_completed(
    task_id=42,
    actual_hours=5.5
)

# Get user performance
perf = PerformanceCalculator.calculate_performance_score(user_id=5)

# Get team performance
team_perf = PerformanceCalculator.calculate_team_performance(org_id=1)

# Identify high performers
high_performers = PerformanceCalculator.identify_high_performers(org_id=1, threshold=80)
```

### API Integration

```javascript
// Complete task and trigger automation
const response = await fetch('/automation/tasks/42/complete', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
        actual_hours: 5.5,
        notes: 'Completed successfully'
    })
});

// Get user performance
const perf = await fetch('/automation/performance/user/5', {
    headers: { 'Authorization': `Bearer ${token}` }
});

// Get team workload status
const workload = await fetch('/automation/workload/team/status', {
    headers: { 'Authorization': `Bearer ${token}` }
});
```

---

## 🔍 Monitoring

### Check Job Status

```python
from celery_app import celery_app

# Get job result
job = celery_app.AsyncResult('job-id')
print(job.status)  # PENDING, STARTED, SUCCESS, FAILURE
print(job.result)  # Result if successful
```

### View Logs

```bash
# Celery worker logs
celery -A celery_app worker --loglevel=info

# Celery beat logs (scheduled tasks)
celery -A celery_app beat --loglevel=info
```

---

## ⚙️ Deployment

### Docker Setup

```dockerfile
# Celery Worker
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["celery", "-A", "celery_app", "worker", "--loglevel=info"]

# Celery Beat
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["celery", "-A", "celery_app", "beat", "--loglevel=info"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  redis:
    image: redis:7
    ports:
      - "6379:6379"
  
  celery-worker:
    build: .
    command: celery -A celery_app worker --loglevel=info
    depends_on:
      - redis
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
  
  celery-beat:
    build: .
    command: celery -A celery_app beat --loglevel=info
    depends_on:
      - redis
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
```

---

## 🐛 Troubleshooting

### Jobs Not Running
- Check Redis is running: `redis-cli ping`
- Check Celery worker: `celery -A celery_app inspect active`
- Check logs for errors

### Performance Scores Not Updating
- Verify assignment records exist
- Check task completion status
- Review Celery task logs

### Notifications Not Sending
- Check notification service configuration
- Verify user email/preferences
- Check notification logs

---

## 📚 Resources

- **Celery Documentation**: https://docs.celeryproject.io
- **Redis Documentation**: https://redis.io/docs
- **Celery Beat**: https://docs.celeryproject.io/en/stable/userguide/periodic-tasks.html

---

**Version**: 1.0
**Last Updated**: May 2024
**Status**: Production Ready
