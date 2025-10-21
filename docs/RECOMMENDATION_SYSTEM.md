# AI Recommendation System

## Overview

An intelligent task recommendation engine that suggests suitable tasks for users based on their skills, completion history, experience level, and current workload.

---

## 🎯 Features

### 1. Skill-Based Matching
- ✅ Calculates skill overlap between user and task
- ✅ Prioritizes tasks matching user expertise
- ✅ Suggests skill-building opportunities

### 2. Completion History Analysis
- ✅ Analyzes past task completion times
- ✅ Calculates success rate on similar tasks
- ✅ Predicts likelihood of on-time completion

### 3. Experience Matching
- ✅ Matches task difficulty to user experience
- ✅ Prevents over/under-challenging tasks
- ✅ Optimizes learning opportunities

### 4. Workload Management
- ✅ Considers current workload
- ✅ Prevents overloading
- ✅ Suggests appropriately-sized tasks

### 5. Personalized Insights
- ✅ Explains why tasks are recommended
- ✅ Provides actionable insights
- ✅ Suggests performance improvements

---

## 📊 Scoring Algorithm

### Recommendation Score Components

```
Score = (
    Skill Overlap × 0.30 +           # 30% - Skill match
    Completion Time Fit × 0.20 +     # 20% - Time match
    Success Rate × 0.20 +            # 20% - Past success
    Workload Fit × 0.15 +            # 15% - Capacity
    Experience Match × 0.15          # 15% - Difficulty match
) × Priority Boost × 100
```

### Components

#### Skill Overlap (30%)
- Percentage of required skills user possesses
- Range: 0-1 (0-100%)
- Higher is better

#### Completion Time Fit (20%)
- How well task difficulty matches user speed
- Range: 0-1 (0-100%)
- Optimal ratio around 1.0

#### Success Rate (20%)
- User's success rate on similar tasks
- Range: 0-1 (0-100%)
- Based on on-time completion

#### Workload Fit (15%)
- How well task fits available capacity
- Range: 0-1 (0-100%)
- Optimal utilization 50-80%

#### Experience Match (15%)
- How well task difficulty matches experience
- Range: 0-1 (0-100%)
- Prevents too easy/hard tasks

#### Priority Boost
- Multiplier based on task priority
- Low: 0.8x, Medium: 1.0x, High: 1.3x
- Additional boost if overdue

---

## 📡 API Endpoints

### Get Recommended Tasks
```
GET /api/recommendations/tasks?top_n=3
Authorization: Bearer <token>

Response: 200 OK
{
    "user_id": 5,
    "recommendations": [
        {
            "task_id": 42,
            "task_title": "Complete Project Proposal",
            "task_description": "Finalize and submit project proposal",
            "project_id": 1,
            "project_name": "Website Redesign",
            "difficulty": 6,
            "priority": "high",
            "due_date": "2024-05-20",
            "required_skills": ["Python", "Django"],
            "recommendation_score": 87.5,
            "components": {
                "skill_overlap": 0.85,
                "completion_time_fit": 0.90,
                "success_rate": 0.92,
                "workload_fit": 0.80,
                "experience_match": 0.88
            }
        }
    ],
    "total": 3
}
```

### Get Personalized Recommendations
```
GET /api/recommendations/tasks/personalized?top_n=5
Authorization: Bearer <token>

Response: 200 OK
{
    "user_id": 5,
    "recommendations": [...],
    "insights": [
        "Great performance! You can handle more challenging tasks.",
        "You have limited capacity. Focus on high-priority tasks."
    ],
    "total_recommendations": 5,
    "generated_at": "2024-05-15T14:30:00"
}
```

### Get Task Recommendation Score
```
GET /api/recommendations/tasks/42/score
Authorization: Bearer <token>

Response: 200 OK
{
    "task_id": 42,
    "user_id": 5,
    "recommendation_score": 87.5,
    "components": {
        "skill_overlap": 0.85,
        "completion_time_fit": 0.90,
        "success_rate": 0.92,
        "workload_fit": 0.80,
        "experience_match": 0.88
    }
}
```

### Get Recommendation Analysis
```
GET /api/recommendations/analysis?top_n=3
Authorization: Bearer <token>

Response: 200 OK
{
    "user_id": 5,
    "analysis": [
        {
            "task_id": 42,
            "task_title": "Complete Project Proposal",
            "score": 87.5,
            "explanation": [
                "Strong skill match (85%)",
                "High success rate on similar tasks (92%)",
                "Good difficulty match for your experience level",
                "High priority task"
            ],
            "components": {...}
        }
    ]
}
```

---

## 🔧 Usage Examples

### Python Integration

```python
from recommendations import RecommendationEngine

# Get top 3 recommendations
recommendations = RecommendationEngine.recommend_tasks_for_user(
    user_id=5,
    top_n=3,
    organization_id=1
)

# Get personalized recommendations with insights
result = RecommendationEngine.get_personalized_recommendations(
    user_id=5,
    top_n=5,
    organization_id=1
)

# Get score for specific task
score = RecommendationEngine.calculate_recommendation_score(
    user_id=5,
    task_id=42
)

# Get component scores
skill_overlap = RecommendationEngine.calculate_skill_overlap(5, 42)
success_rate = RecommendationEngine.calculate_success_rate_on_similar_tasks(5, 42)
```

### JavaScript Integration

```javascript
// Get recommendations
const response = await fetch('/api/recommendations/tasks?top_n=3', {
    headers: { 'Authorization': `Bearer ${token}` }
});
const data = await response.json();

// Display recommendations
data.recommendations.forEach(rec => {
    console.log(`${rec.task_title}: ${rec.recommendation_score.toFixed(1)}`);
});

// Get personalized recommendations
const personalized = await fetch('/api/recommendations/tasks/personalized?top_n=5', {
    headers: { 'Authorization': `Bearer ${token}` }
});
const perData = await personalized.json();

// Display insights
perData.insights.forEach(insight => {
    console.log(`💡 ${insight}`);
});
```

---

## 📊 Scoring Examples

### Example 1: Perfect Match
```
Task: "API Development"
User Skills: Python, Django, REST APIs
Task Skills: Python, Django, REST APIs

Skill Overlap: 100%
Completion Time Fit: 90%
Success Rate: 92%
Workload Fit: 80%
Experience Match: 88%
Priority: High (1.3x boost)

Score = (1.0 × 0.30 + 0.90 × 0.20 + 0.92 × 0.20 + 0.80 × 0.15 + 0.88 × 0.15) × 1.3 × 100
      = 0.8756 × 1.3 × 100
      = 113.8 (capped at 100)
```

### Example 2: Good Match
```
Task: "Database Design"
User Skills: Python, SQL
Task Skills: Python, SQL, Database Design

Skill Overlap: 67%
Completion Time Fit: 75%
Success Rate: 80%
Workload Fit: 70%
Experience Match: 75%
Priority: Medium (1.0x boost)

Score = (0.67 × 0.30 + 0.75 × 0.20 + 0.80 × 0.20 + 0.70 × 0.15 + 0.75 × 0.15) × 1.0 × 100
      = 0.7345 × 100
      = 73.45
```

### Example 3: Poor Match
```
Task: "Mobile App Development"
User Skills: Python, Django
Task Skills: Swift, iOS, Objective-C

Skill Overlap: 0%
Completion Time Fit: 40%
Success Rate: 30%
Workload Fit: 60%
Experience Match: 50%
Priority: Low (0.8x boost)

Score = (0.0 × 0.30 + 0.40 × 0.20 + 0.30 × 0.20 + 0.60 × 0.15 + 0.50 × 0.15) × 0.8 × 100
      = 0.295 × 0.8 × 100
      = 23.6
```

---

## 🔐 Security & Permissions

- ✅ Users can only see recommendations for themselves
- ✅ Recommendations filtered by organization
- ✅ No sensitive data exposed
- ✅ Audit logging for recommendations

---

## 📈 Dashboard Integration

### AI Suggested Tasks Widget
```javascript
// Display recommended tasks
<div class="ai-suggestions">
    <h3>🤖 AI Suggested Tasks</h3>
    <div class="suggestions-list">
        {recommendations.map(rec => (
            <div class="suggestion-card">
                <h4>{rec.task_title}</h4>
                <p>{rec.project_name}</p>
                <div class="score-bar">
                    <div class="score" style={{width: `${rec.recommendation_score}%`}}>
                        {rec.recommendation_score.toFixed(0)}%
                    </div>
                </div>
                <div class="metrics">
                    <span>Skills: {(rec.components.skill_overlap*100).toFixed(0)}%</span>
                    <span>Success: {(rec.components.success_rate*100).toFixed(0)}%</span>
                </div>
            </div>
        ))}
    </div>
</div>
```

---

## 🚀 Performance Considerations

### Optimization Strategies
- Cache recommendations for 1 hour
- Batch calculate scores for multiple tasks
- Index queries on user_id and task status
- Limit to top N results

### Scalability
- Efficient database queries
- Minimal memory footprint
- Parallel score calculation ready
- Caching layer support

---

## 📚 Documentation

- **RECOMMENDATION_SYSTEM.md**: Complete feature documentation
- **API Endpoints**: 4 endpoints with examples
- **Scoring Algorithm**: Detailed breakdown
- **Usage Examples**: Python and JavaScript

---

**Version**: 1.0
**Last Updated**: May 2024
**Status**: Production Ready
