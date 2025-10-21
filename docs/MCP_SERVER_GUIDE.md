# MCP Server Guide for TaskManager

## Overview

The Model Context Protocol (MCP) Server provides structured access to TaskManager data and operations. This allows AI assistants and other tools to query and interact with your task management system programmatically.

## What is MCP?

MCP (Model Context Protocol) is a standardized protocol for AI assistants to access external data sources and tools. It enables:
- Structured data queries
- Real-time information access
- Tool integration
- Standardized communication

## Getting Started

### Installation

The MCP server is included in your TaskManager installation. No additional setup is required beyond the standard TaskManager setup.

### Starting the MCP Server

```bash
# Method 1: Direct Python execution
python mcp_server.py

# Method 2: Using Flask environment
export FLASK_ENV=production
python mcp_server.py

# Method 3: In the background (Unix/Linux)
nohup python mcp_server.py > mcp_server.log 2>&1 &

# Method 4: Using a process manager (Gunicorn)
gunicorn --worker-class=gthread --workers=1 --threads=4 mcp_server:app
```

### Configuration

The MCP server reads from your existing TaskManager configuration:
- Database URL from `.env` or Flask config
- Uses the same database as your Flask application
- Inherits all Flask settings

## Available Methods

### 1. Projects

#### `get_projects`
Get all projects or projects for a specific user.

**Parameters:**
- `user_id` (optional): Filter projects for a specific user

**Example Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "get_projects",
  "params": {
    "user_id": 1
  }
}
```

**Example Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": [
    {
      "id": 1,
      "title": "Website Redesign",
      "description": "Complete redesign of company website",
      "deadline": "2024-06-30",
      "progress": 65,
      "task_count": 20,
      "created_at": "2024-05-01T10:00:00"
    }
  ]
}
```

#### `get_project_details`
Get detailed information about a specific project.

**Parameters:**
- `project_id` (required): Project ID

**Example Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "get_project_details",
  "params": {
    "project_id": 1
  }
}
```

**Example Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "id": 1,
    "title": "Website Redesign",
    "description": "Complete redesign of company website",
    "deadline": "2024-06-30",
    "progress": 65,
    "created_at": "2024-05-01T10:00:00",
    "tasks": [
      {
        "id": 1,
        "title": "Design mockups",
        "status": "Done",
        "priority": "High",
        "due_date": "2024-05-15",
        "assignees": ["john_doe"]
      }
    ],
    "team_members": ["john_doe", "jane_smith"]
  }
}
```

### 2. Tasks

#### `get_tasks`
Get tasks with optional filtering.

**Parameters:**
- `project_id` (optional): Filter by project
- `status` (optional): Filter by status (To Do, In Progress, Done)
- `user_id` (optional): Filter by assigned user

**Example Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "get_tasks",
  "params": {
    "project_id": 1,
    "status": "In Progress"
  }
}
```

#### `get_task_details`
Get detailed information about a specific task.

**Parameters:**
- `task_id` (required): Task ID

**Example Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "get_task_details",
  "params": {
    "task_id": 1
  }
}
```

**Example Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "id": 1,
    "title": "Design mockups",
    "description": "Create UI mockups for the new website",
    "status": "Done",
    "priority": "High",
    "due_date": "2024-05-15",
    "project_id": 1,
    "project_title": "Website Redesign",
    "assignees": [
      {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com"
      }
    ],
    "comments": [
      {
        "id": 1,
        "author": "john_doe",
        "body": "Mockups completed and reviewed",
        "created_at": "2024-05-15T14:30:00"
      }
    ],
    "predecessors": [],
    "successors": [
      {
        "id": 2,
        "title": "Frontend development"
      }
    ]
  }
}
```

#### `get_user_tasks`
Get all tasks assigned to a specific user.

**Parameters:**
- `user_id` (required): User ID
- `status` (optional): Filter by status

**Example Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "get_user_tasks",
  "params": {
    "user_id": 1,
    "status": "In Progress"
  }
}
```

#### `get_overdue_tasks`
Get all overdue tasks.

**Parameters:**
- `project_id` (optional): Filter by project

**Example Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "get_overdue_tasks",
  "params": {}
}
```

#### `get_upcoming_tasks`
Get tasks due in the next N days.

**Parameters:**
- `days` (optional, default: 7): Number of days to look ahead
- `project_id` (optional): Filter by project

**Example Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "method": "get_upcoming_tasks",
  "params": {
    "days": 14,
    "project_id": 1
  }
}
```

### 3. Statistics & Analytics

#### `get_project_statistics`
Get statistics for a project.

**Parameters:**
- `project_id` (required): Project ID

**Example Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 8,
  "method": "get_project_statistics",
  "params": {
    "project_id": 1
  }
}
```

**Example Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 8,
  "result": {
    "project_id": 1,
    "project_title": "Website Redesign",
    "total_tasks": 20,
    "completed_tasks": 13,
    "in_progress_tasks": 5,
    "todo_tasks": 2,
    "completion_percentage": 65,
    "high_priority_tasks": 8,
    "medium_priority_tasks": 10,
    "low_priority_tasks": 2,
    "overdue_tasks": 1,
    "team_members": 3
  }
}
```

#### `get_team_workload`
Get workload distribution across team members.

**Parameters:**
- `project_id` (optional): Filter by project

**Example Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 9,
  "method": "get_team_workload",
  "params": {
    "project_id": 1
  }
}
```

**Example Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 9,
  "result": [
    {
      "user_id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "total_tasks": 8,
      "high_priority": 3,
      "medium_priority": 4,
      "low_priority": 1,
      "workload_score": 17
    },
    {
      "user_id": 2,
      "username": "jane_smith",
      "email": "jane@example.com",
      "total_tasks": 5,
      "high_priority": 2,
      "medium_priority": 2,
      "low_priority": 1,
      "workload_score": 10
    }
  ]
}
```

### 4. Search & Discovery

#### `search_tasks`
Search tasks by title or description.

**Parameters:**
- `query` (required): Search query
- `project_id` (optional): Filter by project

**Example Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 10,
  "method": "search_tasks",
  "params": {
    "query": "design",
    "project_id": 1
  }
}
```

### 5. Dashboard

#### `get_dashboard_summary`
Get a comprehensive dashboard summary for a user.

**Parameters:**
- `user_id` (required): User ID

**Example Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 11,
  "method": "get_dashboard_summary",
  "params": {
    "user_id": 1
  }
}
```

**Example Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 11,
  "result": {
    "user_id": 1,
    "username": "john_doe",
    "total_tasks": 25,
    "pending_tasks": 12,
    "completed_tasks": 13,
    "completed_today": 2,
    "overdue_tasks": 1,
    "projects_count": 3,
    "high_priority_pending": 3,
    "upcoming_tasks_7_days": 5
  }
}
```

## Integration Examples

### Python Client

```python
import json
import subprocess

class TaskManagerMCPClient:
    def __init__(self):
        self.process = subprocess.Popen(
            ['python', 'mcp_server.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        self.request_id = 0
    
    def request(self, method, params=None):
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }
        
        self.process.stdin.write(json.dumps(request) + '\n')
        self.process.stdin.flush()
        
        response = self.process.stdout.readline()
        return json.loads(response)
    
    def get_projects(self, user_id=None):
        return self.request("get_projects", {"user_id": user_id})
    
    def get_tasks(self, project_id=None, status=None, user_id=None):
        return self.request("get_tasks", {
            "project_id": project_id,
            "status": status,
            "user_id": user_id
        })
    
    def close(self):
        self.process.terminate()

# Usage
client = TaskManagerMCPClient()
projects = client.get_projects(user_id=1)
print(projects)
client.close()
```

### JavaScript/Node.js Client

```javascript
const { spawn } = require('child_process');

class TaskManagerMCPClient {
    constructor() {
        this.process = spawn('python', ['mcp_server.py']);
        this.requestId = 0;
        this.callbacks = {};
        
        this.process.stdout.on('data', (data) => {
            const response = JSON.parse(data.toString());
            const callback = this.callbacks[response.id];
            if (callback) {
                callback(response.result || response.error);
                delete this.callbacks[response.id];
            }
        });
    }
    
    request(method, params = {}) {
        return new Promise((resolve) => {
            this.requestId++;
            const request = {
                jsonrpc: "2.0",
                id: this.requestId,
                method: method,
                params: params
            };
            
            this.callbacks[this.requestId] = resolve;
            this.process.stdin.write(JSON.stringify(request) + '\n');
        });
    }
    
    async getProjects(userId = null) {
        return this.request("get_projects", { user_id: userId });
    }
    
    async getTasks(projectId = null, status = null, userId = null) {
        return this.request("get_tasks", {
            project_id: projectId,
            status: status,
            user_id: userId
        });
    }
    
    close() {
        this.process.kill();
    }
}

// Usage
const client = new TaskManagerMCPClient();
client.getProjects(1).then(projects => {
    console.log(projects);
    client.close();
});
```

## Error Handling

The MCP server returns standard JSON-RPC error responses:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32603,
    "message": "Internal error",
    "data": "Project 999 not found"
  }
}
```

### Common Error Codes
- `-32700`: Parse error
- `-32603`: Internal error
- `-32602`: Invalid params
- `-32601`: Method not found

## Performance Considerations

1. **Large Result Sets**: For queries that return many tasks, consider filtering by project or status
2. **Caching**: Implement caching in your client for frequently accessed data
3. **Rate Limiting**: Consider implementing rate limiting for production use
4. **Database Indexing**: Ensure your database has proper indexes for common queries

## Security

1. **Authentication**: The MCP server uses the same database as your Flask app
2. **Authorization**: Implement authorization checks in your client code
3. **Data Validation**: All inputs are validated before database queries
4. **SQL Injection**: Uses SQLAlchemy ORM to prevent SQL injection

## Troubleshooting

### Server won't start
```bash
# Check Python version
python --version  # Should be 3.7+

# Check dependencies
pip list | grep -E "Flask|SQLAlchemy"

# Check database connection
python -c "from app import create_app; app = create_app(); print('OK')"
```

### No response from server
- Check that the server process is running
- Verify the database is accessible
- Check server logs for errors

### Timeout errors
- Increase timeout in your client
- Optimize database queries
- Check database performance

## Advanced Usage

### Streaming Results

For large result sets, you can implement streaming:

```python
def stream_tasks(self, project_id):
    query = Task.query.filter_by(project_id=project_id)
    for task in query.yield_per(100):
        yield {
            "id": task.id,
            "title": task.title,
            "status": task.status
        }
```

### Custom Methods

You can extend the MCP server with custom methods:

```python
def get_custom_report(self, project_id):
    """Custom reporting method"""
    # Your custom logic here
    pass
```

## Future Enhancements

- [ ] WebSocket support for real-time updates
- [ ] Batch operations
- [ ] Subscription support for notifications
- [ ] Advanced filtering and sorting
- [ ] Pagination support
- [ ] Custom field support

---

**Last Updated**: May 2024
**Version**: 1.0
**Status**: Production Ready
