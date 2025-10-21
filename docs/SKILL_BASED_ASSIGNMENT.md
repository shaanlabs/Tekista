# Skill-Based Task Assignment Engine

## Overview

The Skill-Based Task Assignment Engine automatically assigns tasks to the most suitable team members based on their skills, experience, performance, and current workload. This system uses intelligent algorithms to optimize task allocation and improve team productivity.

---

## Features

### 1. User Skill Profiles
- **Skills**: List of technical and soft skills
- **Experience Level**: 1-10 scale
- **Performance Score**: 0-100 scale based on task completion quality
- **Completion Metrics**: Average completion time, tasks completed
- **Workload Tracking**: Current hours, maximum weekly capacity
- **Availability**: Mark users as available/unavailable
- **Preferences**: Preferred task difficulty range

### 2. Intelligent Assignment Algorithm
- **Skill Matching**: Matches required skills with user capabilities
- **Workload Balancing**: Considers current workload and capacity
- **Performance Scoring**: Prioritizes high performers
- **Experience Matching**: Aligns task difficulty with user experience
- **Multiple Strategies**: Choose from skill-match, workload-balance, performance, or hybrid

### 3. Assignment Tracking
- **Assignment History**: Complete record of all assignments
- **Scoring Details**: Skill match, workload, and performance scores
- **Time Estimation**: Predicts completion time based on history
- **Feedback System**: Collect feedback on assignment quality
- **Statistics**: Aggregated metrics for continuous improvement

### 4. Skill Endorsements
- **Peer Endorsements**: Team members can endorse each other's skills
- **Endorsement Levels**: 1-5 scale for skill proficiency
- **Skill Verification**: Community-validated skill levels

---

## Data Models

### UserSkillProfile
```python
{
    'user_id': int,
    'skills': ['Python', 'JavaScript', 'React'],
    'experience_level': 7,  # 1-10
    'performance_score': 85.5,  # 0-100
    'tasks_completed': 42,
    'avg_completion_time': 6.5,  # hours
    'current_workload_hours': 28.0,
    'max_weekly_hours': 40.0,
    'is_available': True,
    'preferred_difficulty_min': 3,
    'preferred_difficulty_max': 8
}
```

### TaskAssignment
```python
{
    'task_id': int,
    'assigned_user_id': int,
    'assignment_strategy': 'hybrid',
    'skill_match_score': 0.85,  # 0-1
    'workload_score': 0.72,  # 0-1
    'performance_score': 0.90,  # 0-1
    'overall_score': 0.82,  # 0-1
    'estimated_completion_hours': 5.5,
    'assignment_reason': 'Excellent skill match | Low workload | High performer',
    'assignment_status': 'active'  # active, completed, cancelled
}
```

### Task Requirements
```python
{
    'required_skills': ['Python', 'Django'],
    'difficulty': 6,  # 1-10
    'priority': 'high',  # low, medium, high
    'status': 'pending'
}
```

---

## Assignment Algorithm

### Scoring Components

#### 1. Skill Match Score (40% weight in hybrid mode)
```
skill_match = matched_skills / required_skills
```
- Minimum 50% match required for assignment
- Case-insensitive matching
- Partial credit for partial matches

#### 2. Workload Score (30% weight)
```
workload_score = 1.0 - (current_hours / max_hours)
```
- Higher score = more available capacity
- Prevents overloading team members
- Considers maximum weekly hours

#### 3. Performance Score (20% weight)
```
performance_score = performance / 100.0
```
- Based on historical task completion quality
- Prioritizes reliable team members
- Normalized to 0-1 range

#### 4. Experience Score (10% weight)
```
experience_score = experience_level / 10.0
```
- Considers user's overall experience
- Helps match task difficulty to capability

#### 5. Difficulty Adjustment
```
adjustment = calculate_difficulty_adjustment(task_difficulty, user_experience)
```
- Multiplier applied to overall score
- Prevents assigning too-difficult or too-easy tasks
- Ranges from 0.5 to 1.5

### Overall Score Calculation

**Hybrid Strategy (Default):**
```
overall_score = (
    0.40 * skill_match +
    0.30 * workload_score +
    0.20 * performance_score +
    0.10 * experience_score
) * difficulty_adjustment
```

**Other Strategies:**
- **Skill Match**: Prioritizes skill_match score
- **Workload Balance**: Prioritizes workload_score
- **Performance**: Prioritizes performance_score

---

## API Endpoints

### User Skill Profile

#### Get Skill Profile
```
GET /assignment/profile
Authorization: Bearer <token>

Response:
{
    "user_id": 1,
    "skills": ["Python", "JavaScript"],
    "experience_level": 7,
    "performance_score": 85.5,
    "tasks_completed": 42,
    "avg_completion_time": 6.5,
    "current_workload_hours": 28.0,
    "max_weekly_hours": 40.0,
    "available_capacity": 12.0,
    "is_overloaded": false,
    "is_available": true
}
```

#### Update Skill Profile
```
PUT /assignment/profile
Authorization: Bearer <token>
Content-Type: application/json

{
    "skills": ["Python", "JavaScript", "React"],
    "experience_level": 8,
    "max_weekly_hours": 45,
    "is_available": true,
    "preferred_difficulty_min": 4,
    "preferred_difficulty_max": 9
}

Response: 200 OK
```

#### Add Skill
```
POST /assignment/profile/skills
Authorization: Bearer <token>
Content-Type: application/json

{
    "skill": "Docker"
}

Response: 200 OK
```

#### Remove Skill
```
DELETE /assignment/profile/skills/Docker
Authorization: Bearer <token>

Response: 200 OK
```

### Task Assignment

#### Auto-Assign Task
```
POST /assignment/tasks/<task_id>/auto-assign
Authorization: Bearer <token>
Content-Type: application/json

{
    "strategy": "hybrid"  # skill_match, workload_balance, performance, hybrid
}

Response: 201 Created
{
    "task_id": 42,
    "assigned_user_id": 5,
    "assigned_user_name": "john_doe",
    "overall_score": 0.82,
    "skill_match": 0.85,
    "workload_score": 0.72,
    "performance_score": 0.90,
    "estimated_completion_hours": 5.5,
    "reason": "Excellent skill match | Low workload | High performer"
}
```

#### Get Assignment Recommendations
```
GET /assignment/tasks/<task_id>/recommendations?top_n=5
Authorization: Bearer <token>

Response:
{
    "task_id": 42,
    "recommendations": [
        {
            "user_id": 5,
            "overall_score": 0.82,
            "skill_match": 0.85,
            "workload_score": 0.72,
            "performance_score": 0.90,
            "estimated_completion_hours": 5.5,
            "reason": "Excellent skill match | Low workload"
        },
        ...
    ]
}
```

#### Reassign Task
```
POST /assignment/tasks/<task_id>/reassign
Authorization: Bearer <token>
Content-Type: application/json

{
    "reason": "Original assignee unavailable"
}

Response: 200 OK
```

#### Complete Assignment
```
POST /assignment/assignments/<assignment_id>/complete
Authorization: Bearer <token>
Content-Type: application/json

{
    "actual_hours": 5.5
}

Response: 200 OK
```

#### Submit Assignment Feedback
```
POST /assignment/assignments/<assignment_id>/feedback
Authorization: Bearer <token>
Content-Type: application/json

{
    "difficulty_rating": 4,  # 1-5
    "skill_match_rating": 5,
    "workload_rating": 4,
    "comments": "Task was well-matched to my skills",
    "suggestions": "Could have more documentation"
}

Response: 201 Created
```

### Skill Endorsements

#### Endorse Skill
```
POST /assignment/users/<user_id>/endorse
Authorization: Bearer <token>
Content-Type: application/json

{
    "skill": "Python",
    "level": 5  # 1-5
}

Response: 201 Created
```

#### Get Skill Endorsements
```
GET /assignment/users/<user_id>/endorsements
Authorization: Bearer <token>

Response:
[
    {
        "skill": "Python",
        "endorsements": [
            {"endorsed_by": "alice", "level": 5},
            {"endorsed_by": "bob", "level": 4}
        ],
        "avg_level": 4.5,
        "total_endorsements": 2
    }
]
```

### Statistics

#### Get Assignment Statistics
```
GET /assignment/statistics
Authorization: Bearer <token>

Response:
{
    "total_assignments": 42,
    "completed_assignments": 38,
    "cancelled_assignments": 2,
    "avg_estimation_accuracy": 0.92,
    "avg_skill_match_score": 0.85,
    "avg_difficulty_assigned": 6.2,
    "avg_completion_time": 5.8,
    "avg_workload_utilization": 0.78,
    "avg_difficulty_rating": 4.1,
    "avg_skill_match_rating": 4.3,
    "avg_workload_rating": 3.9
}
```

#### List Assignments
```
GET /assignment/assignments?page=1&per_page=20&status=active
Authorization: Bearer <token>

Response:
{
    "total": 42,
    "pages": 3,
    "current_page": 1,
    "assignments": [...]
}
```

#### Get Team Statistics
```
GET /assignment/team-statistics
Authorization: Bearer <token>

Response:
[
    {
        "user_id": 1,
        "username": "john_doe",
        "total_assignments": 42,
        "completed_assignments": 38,
        "avg_estimation_accuracy": 0.92,
        "avg_skill_match_score": 0.85,
        "avg_completion_time": 5.8,
        "avg_workload_utilization": 0.78
    }
]
```

---

## Usage Examples

### Python Integration

```python
from assignment import AssignmentService, AssignmentStrategy

# Initialize service
service = AssignmentService(strategy=AssignmentStrategy.HYBRID)

# Auto-assign a task
result = service.auto_assign_task(task_id=42, organization_id=1)

# Get recommendations
recommendations = service.get_assignment_recommendations(
    task_id=42,
    organization_id=1,
    top_n=5
)

# Reassign task
new_result = service.reassign_task(
    task_id=42,
    organization_id=1,
    reason="Original assignee unavailable"
)
```

### Automatic Assignment on Task Creation

```python
from assignment import AssignmentService

def create_task_with_auto_assignment(project_id, title, required_skills, difficulty):
    """Create task and automatically assign it"""
    
    # Create task
    task = Task(
        project_id=project_id,
        title=title,
        required_skills=required_skills,
        difficulty=difficulty,
        status='pending'
    )
    db.session.add(task)
    db.session.commit()
    
    # Auto-assign
    service = AssignmentService()
    assignment = service.auto_assign_task(task.id, project_id.organization_id)
    
    return task, assignment
```

### Update Workload After Task Completion

```python
def complete_task(assignment_id, actual_hours):
    """Complete task and update workload"""
    
    assignment = TaskAssignment.query.get(assignment_id)
    user_profile = assignment.assigned_user.skill_profile
    
    # Update workload
    user_profile.update_workload(
        user_profile.current_workload_hours - actual_hours
    )
    
    # Mark assignment complete
    assignment.mark_completed(actual_hours)
    
    # Update statistics
    stats = AssignmentStatistics.query.filter_by(
        user_id=assignment.assigned_user_id
    ).first()
    if stats:
        stats.update_metrics()
```

---

## Configuration

### Environment Variables

```env
# Assignment Engine
ASSIGNMENT_STRATEGY=hybrid  # skill_match, workload_balance, performance, hybrid
MIN_SKILL_MATCH=0.5  # Minimum 50% skill match required
MAX_WORKLOAD_HOURS=40  # Maximum hours per week

# Scoring Weights (for hybrid strategy)
SKILL_MATCH_WEIGHT=0.40
WORKLOAD_WEIGHT=0.30
PERFORMANCE_WEIGHT=0.20
EXPERIENCE_WEIGHT=0.10
```

---

## Best Practices

### 1. Maintain Accurate Skill Profiles
- Regularly update skills
- Request skill endorsements from colleagues
- Keep experience level current

### 2. Provide Assignment Feedback
- Rate difficulty of assigned tasks
- Comment on skill match quality
- Suggest improvements

### 3. Monitor Workload
- Check available capacity before accepting tasks
- Update workload hours regularly
- Communicate availability changes

### 4. Use Appropriate Strategies
- **Skill Match**: For specialized tasks
- **Workload Balance**: For team fairness
- **Performance**: For critical tasks
- **Hybrid**: For balanced optimization

### 5. Review Statistics
- Monitor estimation accuracy
- Track skill match quality
- Identify improvement areas

---

## Performance Considerations

### Database Optimization
- Index on user_id for fast lookups
- Index on task_id for assignment queries
- Index on assigned_at for sorting

### Caching
- Cache user skill profiles
- Cache assignment statistics
- Invalidate on profile updates

### Scalability
- Batch assignment for multiple tasks
- Async processing for statistics updates
- Pagination for large result sets

---

## Troubleshooting

### No Suitable Users Found
- Check minimum skill match threshold
- Verify users have skill profiles
- Ensure users are available
- Consider lowering difficulty requirement

### Inaccurate Time Estimates
- Collect more historical data
- Update average completion times
- Consider task-specific factors
- Adjust difficulty assessments

### Unbalanced Workload
- Use workload_balance strategy
- Monitor team utilization
- Redistribute tasks manually if needed
- Update max_weekly_hours

---

## Future Enhancements

- [ ] Machine learning for better predictions
- [ ] Team capacity planning
- [ ] Skill gap analysis
- [ ] Training recommendations
- [ ] Burnout detection
- [ ] Skill growth tracking
- [ ] Peer mentoring matching
- [ ] Advanced analytics dashboard

---

**Last Updated**: May 2024
**Version**: 1.0
**Status**: Production Ready
