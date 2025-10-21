# TaskManager AI Features - Quick Reference

## 🚀 Getting Started (5 minutes)

### 1. Install
```bash
pip install -r requirements.txt
```

### 2. Configure
Create `.env`:
```env
ENABLE_AI_FEATURES=true
OPENAI_API_KEY=sk-your-key-here
```

### 3. Run
```bash
flask run
```

### 4. Access
- Open http://localhost:5000
- Click robot icon (🤖) for AI chat
- Go to dashboard for AI features

---

## 💡 Feature Quick Guide

### AI Chat (🤖)
**Location**: Bottom-right corner
**Use**: Ask questions about your tasks
```
"What's pending for Project Alpha?"
"Show me my workload"
"Which tasks are at risk?"
```

### Task Estimation (⏱️)
**Location**: Task creation form
**Use**: Get estimated duration
**Action**: Click "Estimate Duration" button
**Result**: Auto-fills due date

### Natural Language Tasks
**Location**: Quick Add Task modal
**Use**: Create tasks from text
```
"Remind me to finalize UI by Friday"
"High priority: Complete proposal by May 20"
"Follow up with client next week"
```

### AI Summary
**Location**: Dashboard
**Use**: Get project overview
**Feature**: Auto-refreshes every 5 minutes

### AI Suggestions
**Location**: Dashboard sidebar
**Use**: Get productivity recommendations
**Feature**: Personalized based on your patterns

### Workload Visualization
**Location**: Dashboard
**Use**: See team member workload
**Feature**: Identifies overallocated members

---

## 📊 API Endpoints

### Quick API Reference

```bash
# Estimate task duration
curl -X POST http://localhost:5000/ai/api/ai/estimate-duration \
  -H "Content-Type: application/json" \
  -d '{"title":"Complete proposal","project_id":1}'

# Get at-risk tasks
curl http://localhost:5000/ai/api/ai/risks?project_id=1

# Get project summary
curl http://localhost:5000/ai/api/ai/summary?project_id=1

# Create task from text
curl -X POST http://localhost:5000/ai/api/ai/create-task \
  -H "Content-Type: application/json" \
  -d '{"text":"Remind me to follow up by Friday","project_id":1}'

# Get team workload
curl http://localhost:5000/ai/api/ai/workload?project_id=1

# Get AI suggestions
curl http://localhost:5000/ai/api/ai/suggestions

# Chat with AI
curl -X POST http://localhost:5000/ai/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What tasks do I have?"}'
```

---

## 🔌 MCP Server

### Start MCP Server
```bash
python mcp_server.py
```

### Example MCP Request
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "get_projects",
  "params": {"user_id": 1}
}
```

### Common MCP Methods
- `get_projects` - List projects
- `get_tasks` - List tasks
- `get_task_details` - Task info
- `get_user_tasks` - User's tasks
- `get_overdue_tasks` - Overdue tasks
- `get_upcoming_tasks` - Due soon
- `get_project_statistics` - Project stats
- `get_team_workload` - Team workload
- `search_tasks` - Search tasks
- `get_dashboard_summary` - User summary

---

## 🔧 Configuration

### Environment Variables
```env
# Enable/Disable
ENABLE_AI_FEATURES=true

# OpenAI
OPENAI_API_KEY=sk-...
AI_MODEL=gpt-3.5-turbo
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=500
```

### Change AI Model
```env
# Better quality (more expensive)
AI_MODEL=gpt-4

# Faster (cheaper)
AI_MODEL=gpt-3.5-turbo
```

---

## 🐛 Troubleshooting

### AI Chat Not Working
```bash
# Check API key
echo $OPENAI_API_KEY

# Check logs
tail -f flask.log

# Restart app
# Ctrl+C then: flask run
```

### Task Estimation Shows "Not Enough Data"
- Complete some tasks first
- Ensure tasks have due dates
- Wait for historical data to accumulate

### Features Not Showing
- Verify `ENABLE_AI_FEATURES=true`
- Restart Flask app
- Clear browser cache (Ctrl+Shift+Delete)
- Check browser console (F12)

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| `AI_FEATURES.md` | Complete feature reference |
| `AI_SETUP_GUIDE.md` | Detailed setup instructions |
| `MCP_SERVER_GUIDE.md` | MCP Server API reference |
| `IMPLEMENTATION_SUMMARY.md` | Project overview |
| `QUICK_REFERENCE.md` | This file |

---

## 💰 Cost Tracking

### Monitor Usage
1. Visit https://platform.openai.com/account/usage
2. Check daily/monthly usage
3. Set spending limits

### Estimate Costs
- 100 chat messages/day ≈ $0.10-0.50/day
- 1000 estimations/month ≈ $0.50-1.00/month
- **Monthly Average**: $5-20

---

## 🎯 Common Tasks

### Create Task from Chat
1. Click robot icon (🤖)
2. Type: "Add task: Complete report by Friday"
3. AI creates task automatically

### Get Productivity Tips
1. Go to Dashboard
2. Check "AI Suggestions" panel
3. Follow recommended actions

### View Team Workload
1. Go to Dashboard
2. Scroll to "Workload Distribution"
3. See task distribution by priority

### Check Project Health
1. Go to Dashboard
2. Look at "AI Project Summary"
3. Review risk assessment

---

## 🔐 Security Tips

1. **Never commit `.env`** to git
2. **Rotate API keys** regularly
3. **Use environment variables** for secrets
4. **Monitor API usage** for anomalies
5. **Set spending limits** on OpenAI account

---

## 📱 Mobile Access

AI features work on mobile:
- Chat interface is responsive
- Dashboard adapts to screen size
- All features accessible on phones/tablets

---

## ⚡ Performance Tips

1. **Cache Results**: Browser caches AI responses
2. **Batch Operations**: Group multiple requests
3. **Optimize Queries**: Filter by project/status
4. **Monitor Costs**: Check API usage regularly

---

## 🆘 Getting Help

### Check Documentation
1. Read relevant `.md` file
2. Search for your issue
3. Follow troubleshooting steps

### Check Logs
```bash
# Flask logs
tail -f flask.log

# MCP Server logs
tail -f mcp_server.log
```

### Debug Mode
```bash
# Enable debug logging
export FLASK_DEBUG=1
flask run
```

---

## 📞 Quick Support Checklist

- [ ] API key is valid and in `.env`
- [ ] `ENABLE_AI_FEATURES=true` in `.env`
- [ ] Flask app is running
- [ ] Database is accessible
- [ ] Browser cache is cleared
- [ ] Network connection is stable
- [ ] OpenAI account has credits

---

## 🎓 Learning Path

### Beginner
1. Read this quick reference
2. Try AI chat feature
3. Create a task with natural language

### Intermediate
1. Read `AI_FEATURES.md`
2. Use all AI features
3. Monitor costs and usage

### Advanced
1. Read `MCP_SERVER_GUIDE.md`
2. Integrate MCP Server
3. Build custom clients
4. Customize AI behavior

---

## 🚀 Next Steps

1. **Install**: `pip install -r requirements.txt`
2. **Configure**: Create `.env` with API key
3. **Run**: `flask run`
4. **Explore**: Click robot icon and try features
5. **Customize**: Adjust settings in `.env`
6. **Integrate**: Use MCP Server for external tools

---

## 📊 Feature Matrix

| Feature | Web UI | API | MCP | Mobile |
|---------|--------|-----|-----|--------|
| AI Chat | ✅ | ✅ | ❌ | ✅ |
| Task Estimation | ✅ | ✅ | ❌ | ✅ |
| Natural Language | ✅ | ✅ | ❌ | ✅ |
| AI Summary | ✅ | ✅ | ❌ | ✅ |
| Suggestions | ✅ | ✅ | ❌ | ✅ |
| Workload | ✅ | ✅ | ✅ | ✅ |
| Statistics | ✅ | ✅ | ✅ | ✅ |

---

## 🎉 You're All Set!

Your TaskManager now has enterprise-grade AI features. Start using them today!

**Questions?** Check the documentation files or review the code comments.

---

**Last Updated**: May 2024
**Quick Reference Version**: 1.0
