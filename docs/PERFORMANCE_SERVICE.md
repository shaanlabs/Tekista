# Performance Tracking Service

## Overview

A comprehensive performance tracking system that automatically calculates and logs user metrics, performance scores, and analytics data for dashboards and reporting.

---

## 🎯 Features

### 1. Automatic Metrics Calculation
- ✅ Completion speed (days early/late)
- ✅ On-time completion ratio
- ✅ Skill accuracy (task-skill match)
- ✅ Difficulty factor (average task difficulty)
- ✅ Average completion time

### 2. Performance Scoring
- ✅ Weighted formula: (50% on-time + 30% skill + 20% difficulty)
- ✅ Automatic score calculation on task completion
- ✅ Score change tracking
- ✅ Historical score trends

### 3. Performance Logging
- ✅ Detailed performance logs for each task
- ✅ Historical data for analytics
- ✅ Trend analysis
- ✅ Performance snapshots

### 4. Analytics & Reporting
- ✅ User performance summary
- ✅ Team performance comparison
- ✅ Performance trends and charts
- ✅ Distribution analysis
- ✅ Performance statistics

### 5. Achievements & Milestones
- ✅ Performance milestones
- ✅ Achievement badges
- ✅ Performance comparisons
- ✅ Leaderboards

---

## 📊 Performance Score Formula

```
Performance Score = (
    On-Time Ratio × 0.5 +      # 50% weight
    Skill Accuracy × 0.3 +     # 30% weight
    Difficulty Factor × 0.2    # 20% weight
) × 100
```

### Components

#### On-Time Ratio (50%)
- Percentage of tasks completed by deadline
- Range: 0-1 (0-100%)
- Higher is better

#### Skill Accuracy (30%)
- Average skill match for completed tasks
- Range: 0-1 (0-100%)
- Measures how well tasks matched user skills

#### Difficulty Factor (20%)
- Average difficulty of completed tasks
- Range: 0-1 (0-10 scale normalized)
- Rewards completing harder tasks

---

## 📁 Data Models

### PerformanceLog
Stores detailed performance metrics for each task completion

```python
{
    'id': int,
    'user_id': int,
    'assignment_id': int,
    'tasks_completed': int,
    'on_time_ratio': float,  # 0-1
    'skill_accuracy': float,  # 0-1
    'difficulty_factor': float,  # 0-1
    'avg_completion_time': float,  # hours
    'avg_completion_speed': float,  # days early/late
    'performance_score': float,  # 0-100
    'score_change': float,  # change from previous
    'created_at': datetime
}
```

### PerformanceSnapshot
Daily performance snapshot for trend analysis

```python
{
    'id': int,
    'user_id': int,
    'snapshot_date': date,
    'tasks_completed_today': int,
    'cumulative_tasks': int,
    'daily_on_time_ratio': float,
    'cumulative_on_time_ratio': float,
    'daily_performance_score': float,
    'cumulative_performance_score': float,
    'created_at': datetime
}
```

### PerformanceMilestone
Track achievements and milestones

```python
{
    'id': int,
    'user_id': int,
    'milestone_type': str,  # e.g., "100_tasks", "perfect_week"
    'milestone_name': str,
    'description': str,
    'achieved_value': float,
    'achievement_data': dict,
    'achieved_at': datetime
}
```

### PerformanceBadge
Badges earned based on performance

```python
{
    'id': int,
    'user_id': int,
    'badge_name': str,
    'badge_description': str,
    'badge_icon': str,
    'criteria': str,
    'criteria_value': float,
    'is_active': bool,
    'earned_at': datetime
}
```

---

## 📡 API Endpoints

### User Performance

#### Get User Performance
```
GET /api/performance/user/<user_id>
Authorization: Bearer <token>

Response: 200 OK
{
    "user_id": 5,
    "username": "john_doe",
    "current_performance_score": 87.5,
    "tasks_completed": 42,
    "avg_completion_time": 5.8,
    "experience_level": 7,
    "latest_metrics": {
        "on_time_ratio": 0.92,
        "skill_accuracy": 0.85,
        "difficulty_factor": 0.75,
        "avg_completion_speed": 1.2
    },
    "trend": {
        "direction": "↑",
        "change": 3.5,
        "period_days": 30
    }
}
```

#### Get User Performance Summary
```
GET /api/performance/user/<user_id>/summary
Authorization: Bearer <token>

Response: 200 OK
(Same as above)
```

#### Get User Performance History
```
GET /api/performance/user/<user_id>/history?days=30&limit=100
Authorization: Bearer <token>

Response: 200 OK
{
    "user_id": 5,
    "period_days": 30,
    "total_entries": 15,
    "entries": [
        {
            "id": 1,
            "created_at": "2024-05-15T14:30:00",
            "tasks_completed": 42,
            "on_time_ratio": 0.92,
            "skill_accuracy": 0.85,
            "difficulty_factor": 0.75,
            "avg_completion_time": 5.8,
            "avg_completion_speed": 1.2,
            "performance_score": 87.5,
            "score_change": 2.1
        }
    ]
}
```

#### Get User Performance Trends
```
GET /api/performance/user/<user_id>/trends?days=90
Authorization: Bearer <token>

Response: 200 OK
{
    "user_id": 5,
    "period_days": 90,
    "data_points": 30,
    "dates": ["2024-02-15", "2024-02-16", ...],
    "performance_scores": [82.1, 83.5, 84.2, ...],
    "on_time_ratios": [85.0, 87.5, 90.0, ...],
    "skill_accuracies": [78.0, 80.0, 82.0, ...],
    "difficulty_factors": [70.0, 72.0, 75.0, ...],
    "statistics": {
        "average_score": 85.3,
        "max_score": 92.1,
        "min_score": 78.5,
        "score_range": 13.6
    }
}
```

#### Get User Metrics
```
GET /api/performance/user/<user_id>/metrics
Authorization: Bearer <token>

Response: 200 OK
{
    "user_id": 5,
    "performance_score": 87.5,
    "tasks_completed": 42,
    "avg_completion_time": 5.8,
    "experience_level": 7,
    "metrics": {
        "on_time_ratio": 0.92,
        "skill_accuracy": 0.85,
        "difficulty_factor": 0.75,
        "avg_completion_speed": 1.2
    },
    "trend": {
        "direction": "↑",
        "change": 3.5,
        "period_days": 30
    }
}
```

### Team Performance

#### Get Team Performance
```
GET /api/performance/team
Authorization: Bearer <token>

Response: 200 OK
{
    "organization_id": 1,
    "team_size": 8,
    "average_performance_score": 82.3,
    "top_performers": [
        {
            "user_id": 5,
            "username": "john_doe",
            "current_performance_score": 87.5,
            ...
        }
    ],
    "all_members": [...]
}
```

#### Get Top Performers
```
GET /api/performance/team/top-performers?limit=10
Authorization: Bearer <token>

Response: 200 OK
{
    "organization_id": 1,
    "limit": 10,
    "count": 8,
    "top_performers": [...]
}
```

#### Compare Team Performance
```
GET /api/performance/team/comparison?user_id_1=5&user_id_2=7&days=30
Authorization: Bearer <token>

Response: 200 OK
{
    "comparison_period_days": 30,
    "user_1": {...},
    "user_2": {...},
    "difference": {
        "score_difference": 5.2,
        "winner": "user_1"
    }
}
```

### Analytics

#### Get Performance Distribution
```
GET /api/performance/analytics/distribution
Authorization: Bearer <token>

Response: 200 OK
{
    "organization_id": 1,
    "total_members": 8,
    "average_score": 82.3,
    "distribution": {
        "0-20": 0,
        "20-40": 0,
        "40-60": 1,
        "60-80": 4,
        "80-100": 3
    },
    "scores": [87.5, 85.2, 82.1, ...]
}
```

#### Get Team Performance Trends
```
GET /api/performance/analytics/trends?days=30
Authorization: Bearer <token>

Response: 200 OK
{
    "organization_id": 1,
    "period_days": 30,
    "team_members": 8,
    "trends": [
        {
            "user_id": 5,
            "username": "john_doe",
            "trends": {...}
        }
    ]
}
```

#### Get Performance Statistics
```
GET /api/performance/statistics
Authorization: Bearer <token>

Response: 200 OK
{
    "organization_id": 1,
    "total_members": 8,
    "statistics": {
        "average_score": 82.3,
        "median_score": 83.1,
        "std_deviation": 4.2,
        "min_score": 72.5,
        "max_score": 92.1,
        "score_range": 19.6
    }
}
```

### Performance Logs

#### Get Performance Logs
```
GET /api/performance/logs?page=1&per_page=50&user_id=5
Authorization: Bearer <token>

Response: 200 OK
{
    "total": 150,
    "pages": 3,
    "current_page": 1,
    "logs": [...]
}
```

### Performance Snapshots

#### Get Performance Snapshots
```
GET /api/performance/snapshots/<user_id>?days=30
Authorization: Bearer <token>

Response: 200 OK
{
    "user_id": 5,
    "period_days": 30,
    "snapshots": [
        {
            "date": "2024-05-15",
            "tasks_completed_today": 3,
            "cumulative_tasks": 42,
            "daily_on_time_ratio": 1.0,
            "cumulative_on_time_ratio": 0.92,
            "daily_performance_score": 90.0,
            "cumulative_performance_score": 87.5
        }
    ]
}
```

### Export

#### Export User Performance
```
GET /api/performance/export/user/<user_id>?format=json
Authorization: Bearer <token>

Response: 200 OK
{
    "summary": {...},
    "history": [...],
    "trends": {...},
    "export_date": "2024-05-15T14:30:00"
}
```

---

## 🔧 Usage Examples

### Python Integration

```python
from performance import PerformanceService

# Update user performance after task completion
result = PerformanceService.update_user_performance(
    user_id=5,
    assignment_id=42
)

# Get user performance summary
summary = PerformanceService.get_user_performance_summary(user_id=5)

# Get performance history
history = PerformanceService.get_user_performance_history(user_id=5, days=30)

# Get performance trends
trends = PerformanceService.get_performance_trends(user_id=5, days=90)

# Get team performance
team_perf = PerformanceService.get_team_performance_summary(org_id=1)
```

### API Integration

```javascript
// Get user performance
const response = await fetch('/api/performance/user/5', {
    headers: { 'Authorization': `Bearer ${token}` }
});
const data = await response.json();

// Get performance trends for chart
const trends = await fetch('/api/performance/user/5/trends?days=90', {
    headers: { 'Authorization': `Bearer ${token}` }
});
const trendData = await trends.json();

// Get team performance
const team = await fetch('/api/performance/team', {
    headers: { 'Authorization': `Bearer ${token}` }
});
const teamData = await team.json();
```

---

## 📊 Metrics Calculation Examples

### Example 1: Perfect Performance
```
User: john_doe
- Tasks: 10/10 on time (100%)
- Skill match: 95%
- Avg difficulty: 8/10 (80%)

Score = (1.0 × 0.5 + 0.95 × 0.3 + 0.8 × 0.2) × 100
      = (0.5 + 0.285 + 0.16) × 100
      = 0.945 × 100
      = 94.5
```

### Example 2: Average Performance
```
User: jane_smith
- Tasks: 8/10 on time (80%)
- Skill match: 75%
- Avg difficulty: 5/10 (50%)

Score = (0.8 × 0.5 + 0.75 × 0.3 + 0.5 × 0.2) × 100
      = (0.4 + 0.225 + 0.1) × 100
      = 0.725 × 100
      = 72.5
```

---

## 🔐 Security & Permissions

### Required Permissions
- `view_team` - View team performance
- `view_audit_log` - View performance logs

### Authorization Checks
- Users can only view their own performance
- Team leads can view team performance
- Managers can view analytics

---

## 📈 Dashboard Integration

### Performance Widget
```javascript
// Display user performance score
<div class="performance-widget">
    <h3>Your Performance</h3>
    <div class="score">87.5</div>
    <div class="metrics">
        <span>On-Time: 92%</span>
        <span>Skill Match: 85%</span>
        <span>Difficulty: 75%</span>
    </div>
</div>
```

### Performance Chart
```javascript
// Chart.js configuration
{
    type: 'line',
    data: {
        labels: trendData.dates,
        datasets: [{
            label: 'Performance Score',
            data: trendData.performance_scores,
            borderColor: '#667eea',
            tension: 0.4
        }]
    }
}
```

### Team Leaderboard
```javascript
// Display top performers
<table class="leaderboard">
    <tr>
        <th>Rank</th>
        <th>Name</th>
        <th>Score</th>
        <th>Tasks</th>
    </tr>
    <!-- Populated from API -->
</table>
```

---

## 🚀 Deployment

### Database Migrations
```bash
flask db migrate -m "Add performance tables"
flask db upgrade
```

### Celery Integration
```python
# Automatic performance update on task completion
@celery_app.task
def update_performance_on_completion(user_id, assignment_id):
    PerformanceService.update_user_performance(user_id, assignment_id)
```

---

## 📚 Documentation

- **PERFORMANCE_SERVICE.md**: Complete feature documentation
- **API Endpoints**: 20+ endpoints for performance tracking
- **Data Models**: 4 comprehensive models
- **Usage Examples**: Python and JavaScript examples

---

**Version**: 1.0
**Last Updated**: May 2024
**Status**: Production Ready
