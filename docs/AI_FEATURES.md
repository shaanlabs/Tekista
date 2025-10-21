# AI & Automation Features Documentation

## Overview

This document describes all the AI and automation features added to the TaskManager application. These features leverage machine learning and natural language processing to provide intelligent task management capabilities.

## Features Implemented

### 1. 🤖 Smart Suggestions

#### AI Task Estimation
- **Functionality**: Predicts how long a task will take based on historical task data
- **How it works**: Analyzes completed tasks in the same project to calculate average duration
- **API Endpoint**: `POST /ai/api/ai/estimate-duration`
- **Parameters**: 
  - `title` (string): Task title
  - `description` (string): Task description
  - `project_id` (int, optional): Project ID for context
- **Response**: `{ "estimated_days": 3.5 }`

#### Auto Task Assignment
- **Functionality**: Suggests optimal task assignments based on workload balance
- **How it works**: Analyzes current workload per team member and suggests assignments
- **API Endpoint**: `GET /ai/api/ai/workload?project_id=<id>`
- **Response**: Array of team members with workload metrics

#### Deadline Prediction
- **Functionality**: Predicts which tasks might go overdue
- **How it works**: Uses task creation date, due date, and current progress to calculate risk
- **API Endpoint**: `GET /ai/api/ai/risks?project_id=<id>`
- **Response**: Array of at-risk tasks with risk scores

### 2. 🪄 AI Assistance

#### AI Summary Generator
- **Functionality**: Generates natural language summaries of project status
- **How it works**: Analyzes project progress, recent tasks, and deadline risks
- **API Endpoint**: `GET /ai/api/ai/summary?project_id=<id>`
- **Response**: 
```json
{
  "summary": "Project: Website Redesign\nProgress: 65% (13/20 tasks completed)\nRecent tasks:\n- ✅ Design mockups (Due: 2024-05-10)\n- ⏳ Frontend development (Due: 2024-05-15)\n- 📝 Backend API (Due: 2024-05-20)\n\n⚠️ Tasks at risk of missing deadlines:\n- Complete Project Proposal (85% risk, 2 days left)"
}
```

#### AI Chatbot Assistant
- **Functionality**: Interactive AI assistant for task management queries
- **How it works**: Uses OpenAI's GPT-3.5-turbo with task context
- **API Endpoint**: `POST /ai/api/ai/chat`
- **Parameters**: `{ "message": "What's pending for Project Alpha?" }`
- **Response**: 
```json
{
  "response": "You have 5 pending tasks for Project Alpha:\n1. Complete UI mockups (Due: May 15)\n2. Setup database (Due: May 18)\n3. API integration (Due: May 20)\n4. Testing phase (Due: May 25)\n5. Documentation (Due: May 28)"
}
```

#### Natural Language Task Creation
- **Functionality**: Creates tasks from natural language input
- **How it works**: Parses natural language to extract task details (title, due date, priority)
- **API Endpoint**: `POST /ai/api/ai/create-task`
- **Parameters**: 
```json
{
  "text": "Remind me to finalize UI by Friday",
  "project_id": 1
}
```
- **Response**: `{ "success": true, "task_id": 42 }`
- **Examples**:
  - "Remind me to finalize UI by Friday" → Creates task due Friday
  - "High priority: Complete project proposal by May 20" → Creates high-priority task
  - "Follow up with client next week" → Creates task for next week

### 3. 📊 AI Insights

#### Productivity Heatmaps
- **Functionality**: Identifies peak productive hours and days
- **How it works**: Analyzes task completion patterns by time of day and day of week
- **Display**: Visual heatmap showing productivity levels
- **Insights**: Recommendations for scheduling focus time

#### Employee Performance Analytics
- **Functionality**: Tracks and visualizes team member performance
- **Metrics**:
  - Tasks completed per week/month
  - Average task completion time
  - Task completion rate (%)
  - Priority distribution
- **Visualization**: Trend graphs and charts
- **API Endpoint**: `GET /ai/api/ai/workload`

#### Anomaly Detection
- **Functionality**: Highlights unusual patterns in task management
- **Detects**:
  - Sudden drop in task completion rate
  - Unusual workload spikes
  - Missed deadline patterns
  - Resource overallocation
- **Alerts**: Proactive notifications when anomalies are detected

## Configuration

### Environment Variables

Add these to your `.env` file to enable AI features:

```env
# Enable AI Features
ENABLE_AI_FEATURES=true

# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key-here

# AI Model Settings
AI_MODEL=gpt-3.5-turbo
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=500
```

### Getting an OpenAI API Key

1. Visit [OpenAI Platform](https://platform.openai.com)
2. Sign up or log in to your account
3. Navigate to API keys section
4. Create a new API key
5. Copy the key and add it to your `.env` file

## Frontend Components

### AI Chat Interface

Located in the bottom-right corner of the application:
- **Toggle Button**: Click the robot icon to open/close the chat
- **Features**:
  - Real-time chat with AI assistant
  - Context-aware responses based on user's tasks
  - Message history during the session
  - Typing indicators

### Dashboard Components

#### AI Summary Card
- Displays AI-generated project summary
- Auto-refreshes every 5 minutes
- Manual refresh button available

#### AI Suggestions Panel
- Personalized productivity recommendations
- Based on user's task patterns and workload
- Actionable suggestions with quick actions

#### Workload Visualization
- Bar chart showing task distribution by priority
- Team member workload comparison
- Identifies overallocated team members

#### AI Insights Modal
- Comprehensive analytics dashboard
- Three tabs: Productivity, Risks, Suggestions
- Visual charts and trend analysis

## API Endpoints

### Task Estimation
```
POST /ai/api/ai/estimate-duration
Content-Type: application/json

{
  "title": "Complete project proposal",
  "description": "Finalize and submit project proposal",
  "project_id": 1
}

Response: { "estimated_days": 3.5 }
```

### Deadline Risks
```
GET /ai/api/ai/risks?project_id=1

Response: [
  {
    "task_id": 5,
    "task_title": "Complete Project Proposal",
    "risk_score": 85,
    "days_remaining": 2
  }
]
```

### Project Summary
```
GET /ai/api/ai/summary?project_id=1

Response: { "summary": "..." }
```

### Create Task from Natural Language
```
POST /ai/api/ai/create-task
Content-Type: application/json

{
  "text": "Remind me to finalize UI by Friday",
  "project_id": 1
}

Response: { "success": true, "task_id": 42 }
```

### Workload Analysis
```
GET /ai/api/ai/workload?project_id=1

Response: [
  {
    "user_id": 1,
    "username": "john_doe",
    "total_tasks": 8,
    "high_priority": 2,
    "medium_priority": 4,
    "low_priority": 2,
    "workload_score": 14
  }
]
```

### AI Suggestions
```
GET /ai/api/ai/suggestions?user_id=1

Response: {
  "suggestions": [
    "Schedule focus time tomorrow morning for 'Complete Project Proposal'",
    "Consider delegating 'Prepare Meeting Notes' to a team member",
    "Try time blocking for deep work sessions"
  ]
}
```

### Chat with AI
```
POST /ai/api/ai/chat
Content-Type: application/json

{
  "message": "What's pending for Project Alpha?"
}

Response: {
  "response": "You have 5 pending tasks for Project Alpha..."
}
```

## JavaScript API

### AIChat Class

```javascript
// Initialize AI Chat
const aiChat = new AIChat();

// Toggle chat window
aiChat.toggleChat();

// Send message
aiChat.sendMessage();

// Add message to chat
aiChat.addMessage('user', 'Hello');
aiChat.addMessage('assistant', 'Hi there!');
```

### AITaskAssistant Class

```javascript
// Initialize Task Assistant
const taskAssistant = new AITaskAssistant();

// Estimate task duration
taskAssistant.estimateTaskDuration();

// Show toast notification
taskAssistant.showToast('Task created successfully!', 'success');
```

### Global Functions

```javascript
// Load AI summary
loadAISummary();

// Load AI suggestions
loadAISuggestions();

// Load workload visualization
loadWorkloadVisualization();

// Refresh AI summary
refreshAISummary();
```

## File Structure

```
tekista-project/
├── ai/
│   ├── __init__.py          # AI Assistant class with core features
│   └── routes.py            # API endpoints for AI features
├── static/
│   ├── css/
│   │   └── ai-features.css  # AI UI styling
│   └── js/
│       └── ai-features.js   # AI frontend JavaScript
├── templates/
│   ├── base.html            # Updated with AI chat interface
│   └── dashboard.html       # Dashboard with AI components
├── config.py                # Updated with AI configuration
├── app.py                   # Updated to register AI blueprint
└── requirements.txt         # Updated with AI dependencies
```

## Usage Examples

### Example 1: Task Estimation
```javascript
// User enters task title and clicks "Estimate Duration"
const title = "Complete project proposal";
const description = "Finalize and submit the project proposal";

fetch('/ai/api/ai/estimate-duration', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ title, description, project_id: 1 })
})
.then(res => res.json())
.then(data => {
  console.log(`Estimated: ${data.estimated_days} days`);
  // Auto-fill due date
  const dueDate = new Date();
  dueDate.setDate(dueDate.getDate() + Math.ceil(data.estimated_days));
  document.querySelector('input[name="due_date"]').value = 
    dueDate.toISOString().split('T')[0];
});
```

### Example 2: Natural Language Task Creation
```javascript
// User types: "Remind me to follow up with client by Friday"
const text = "Remind me to follow up with client by Friday";

fetch('/ai/api/ai/create-task', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ text, project_id: 1 })
})
.then(res => res.json())
.then(data => {
  if (data.success) {
    showToast('Task created successfully!', 'success');
    // Reload page to show new task
    setTimeout(() => window.location.reload(), 1000);
  }
});
```

### Example 3: Chat with AI Assistant
```javascript
// User types message in chat
const message = "What's pending for Project Alpha?";

fetch('/ai/api/ai/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message })
})
.then(res => res.json())
.then(data => {
  // Display AI response in chat
  aiChat.addMessage('assistant', data.response);
});
```

## Troubleshooting

### OpenAI API Key Not Working
- Verify the API key is correct in `.env`
- Check that the API key has appropriate permissions
- Ensure your OpenAI account has available credits

### AI Features Not Appearing
- Verify `ENABLE_AI_FEATURES=true` in `.env`
- Check browser console for JavaScript errors
- Ensure all dependencies are installed: `pip install -r requirements.txt`

### Chat Not Responding
- Check that OpenAI API key is configured
- Verify network connectivity
- Check server logs for error messages
- Ensure rate limits haven't been exceeded

### Task Estimation Not Working
- Ensure there are completed tasks in the project for historical data
- Check that tasks have due dates set
- Verify the project has enough task history

## Future Enhancements

- [ ] Integration with calendar systems (Google Calendar, Outlook)
- [ ] Advanced ML models for better predictions
- [ ] Team collaboration AI features
- [ ] Automated task prioritization
- [ ] Integration with communication tools (Slack, Teams)
- [ ] Advanced anomaly detection with alerts
- [ ] Predictive resource allocation
- [ ] AI-powered meeting notes summarization

## Security Considerations

1. **API Key Security**:
   - Never commit `.env` files with API keys
   - Use environment variables in production
   - Rotate API keys regularly

2. **Data Privacy**:
   - Task data is only used for AI processing within your instance
   - No data is stored by OpenAI beyond the API call
   - Consider data sensitivity when enabling AI features

3. **Rate Limiting**:
   - Implement rate limiting on AI endpoints
   - Monitor API usage to avoid unexpected charges
   - Set spending limits on OpenAI account

## Support

For issues or questions about AI features:
1. Check this documentation
2. Review the troubleshooting section
3. Check server logs for error messages
4. Contact the development team

---

**Last Updated**: May 2024
**Version**: 1.0
**Status**: Production Ready
