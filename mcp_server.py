#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Server for TaskManager
Provides structured access to task management data and operations
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Optional
from sqlalchemy.exc import SQLAlchemyError

from app import create_app
from models import Comment, Project, Task, User, db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskManagerMCPServer:
    """MCP Server for TaskManager application"""
    
    def __init__(self):
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def get_projects(self, user_id: Optional[int] = None) -> list:
        """Get all projects or projects for a specific user"""
        try:
            if user_id:
                user = User.query.get(user_id)
                if not user:
                    return {"error": f"User {user_id} not found"}
                projects = user.projects
            else:
                projects = Project.query.all()
            
            return [{
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "deadline": p.deadline.isoformat() if p.deadline else None,
                "progress": p.progress(),
                "task_count": len(p.tasks),
                "created_at": p.created_at.isoformat()
            } for p in projects]
        except SQLAlchemyError as e:
            logger.error("Error getting projects: %s", e)
            return {"error": str(e)}
    
    def get_project_details(self, project_id: int) -> dict:
        """Get detailed information about a specific project"""
        try:
            project = Project.query.get(project_id)
            if not project:
                return {"error": f"Project {project_id} not found"}
            
            return {
                "id": project.id,
                "title": project.title,
                "description": project.description,
                "deadline": project.deadline.isoformat() if project.deadline else None,
                "progress": project.progress(),
                "created_at": project.created_at.isoformat(),
                "tasks": [{
                    "id": t.id,
                    "title": t.title,
                    "status": t.status,
                    "priority": t.priority,
                    "due_date": t.due_date.isoformat() if t.due_date else None,
                    "assignees": [u.username for u in t.assignees]
                } for t in project.tasks],
                "team_members": [u.username for u in project.users]
            }
        except SQLAlchemyError as e:
            logger.error("Error getting project details: %s", e)
            return {"error": str(e)}
    
    def get_tasks(self, project_id: Optional[int] = None, status: Optional[str] = None, 
                  user_id: Optional[int] = None) -> list:
        """Get tasks with optional filtering"""
        try:
            query = Task.query
            
            if project_id:
                query = query.filter_by(project_id=project_id)
            
            if status:
                query = query.filter_by(status=status)
            
            if user_id:
                query = query.join(Task.assignees).filter(User.id == user_id)
            
            tasks = query.all()
            
            return [{
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "status": t.status,
                "priority": t.priority,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "project_id": t.project_id,
                "project_title": t.project.title if t.project else None,
                "assignees": [u.username for u in t.assignees],
                "created_at": t.created_at.isoformat() if hasattr(t, 'created_at') else None
            } for t in tasks]
        except SQLAlchemyError as e:
            logger.error("Error getting tasks: %s", e)
            return {"error": str(e)}
    
    def get_task_details(self, task_id: int) -> dict:
        """Get detailed information about a specific task"""
        try:
            task = Task.query.get(task_id)
            if not task:
                return {"error": f"Task {task_id} not found"}
            
            return {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "priority": task.priority,
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "project_id": task.project_id,
                "project_title": task.project.title if task.project else None,
                "assignees": [{"id": u.id, "username": u.username, "email": u.email} for u in task.assignees],
                "comments": [{
                    "id": c.id,
                    "author": c.author.username if c.author else "Unknown",
                    "body": c.body,
                    "created_at": c.created_at.isoformat()
                } for c in task.comments],
                "predecessors": [{"id": p.id, "title": p.title} for p in task.predecessors],
                "successors": [{"id": s.id, "title": s.title} for s in task.successors]
            }
        except SQLAlchemyError as e:
            logger.error("Error getting task details: %s", e)
            return {"error": str(e)}
    
    def get_user_tasks(self, user_id: int, status: Optional[str] = None) -> list:
        """Get all tasks assigned to a specific user"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {"error": f"User {user_id} not found"}
            
            tasks = user.tasks
            
            if status:
                tasks = [t for t in tasks if t.status == status]
            
            return [{
                "id": t.id,
                "title": t.title,
                "status": t.status,
                "priority": t.priority,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "project_title": t.project.title if t.project else None,
                "days_until_due": (t.due_date - datetime.utcnow().date()).days if t.due_date else None
            } for t in tasks]
        except SQLAlchemyError as e:
            logger.error("Error getting user tasks: %s", e)
            return {"error": str(e)}
    
    def get_overdue_tasks(self, project_id: Optional[int] = None) -> list:
        """Get all overdue tasks"""
        try:
            query = Task.query.filter(
                Task.status != 'Done',
                Task.due_date < datetime.utcnow().date()
            )
            
            if project_id:
                query = query.filter_by(project_id=project_id)
            
            tasks = query.all()
            
            return [{
                "id": t.id,
                "title": t.title,
                "status": t.status,
                "priority": t.priority,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "project_title": t.project.title if t.project else None,
                "days_overdue": (datetime.utcnow().date() - t.due_date).days,
                "assignees": [u.username for u in t.assignees]
            } for t in tasks]
        except SQLAlchemyError as e:
            logger.error("Error getting overdue tasks: %s", e)
            return {"error": str(e)}
    
    def get_upcoming_tasks(self, days: int = 7, project_id: Optional[int] = None) -> list:
        """Get tasks due in the next N days"""
        try:
            today = datetime.utcnow().date()
            future_date = today + timedelta(days=days)
            
            query = Task.query.filter(
                Task.status != 'Done',
                Task.due_date >= today,
                Task.due_date <= future_date
            ).order_by(Task.due_date.asc())
            
            if project_id:
                query = query.filter_by(project_id=project_id)
            
            tasks = query.all()
            
            return [{
                "id": t.id,
                "title": t.title,
                "status": t.status,
                "priority": t.priority,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "project_title": t.project.title if t.project else None,
                "days_until_due": (t.due_date - today).days,
                "assignees": [u.username for u in t.assignees]
            } for t in tasks]
        except SQLAlchemyError as e:
            logger.error("Error getting upcoming tasks: %s", e)
            return {"error": str(e)}
    
    def get_project_statistics(self, project_id: int) -> dict:
        """Get statistics for a project"""
        try:
            project = Project.query.get(project_id)
            if not project:
                return {"error": f"Project {project_id} not found"}
            
            tasks = project.tasks
            completed = sum(1 for t in tasks if t.status == 'Done')
            in_progress = sum(1 for t in tasks if t.status == 'In Progress')
            todo = sum(1 for t in tasks if t.status == 'To Do')
            
            high_priority = sum(1 for t in tasks if t.priority == 'High')
            medium_priority = sum(1 for t in tasks if t.priority == 'Medium')
            low_priority = sum(1 for t in tasks if t.priority == 'Low')
            
            overdue = sum(1 for t in tasks if t.status != 'Done' and t.due_date and t.due_date < datetime.utcnow().date())
            
            return {
                "project_id": project_id,
                "project_title": project.title,
                "total_tasks": len(tasks),
                "completed_tasks": completed,
                "in_progress_tasks": in_progress,
                "todo_tasks": todo,
                "completion_percentage": (completed / len(tasks) * 100) if tasks else 0,
                "high_priority_tasks": high_priority,
                "medium_priority_tasks": medium_priority,
                "low_priority_tasks": low_priority,
                "overdue_tasks": overdue,
                "team_members": len(project.users)
            }
        except SQLAlchemyError as e:
            logger.error("Error getting project statistics: %s", e)
            return {"error": str(e)}
    
    def get_team_workload(self, project_id: Optional[int] = None) -> list:
        """Get workload distribution across team members"""
        try:
            if project_id:
                project = Project.query.get(project_id)
                if not project:
                    return {"error": f"Project {project_id} not found"}
                users = project.users
            else:
                users = User.query.all()
            
            workload_data = []
            for user in users:
                tasks = [t for t in user.tasks if t.status != 'Done']
                high_priority = sum(1 for t in tasks if t.priority == 'High')
                medium_priority = sum(1 for t in tasks if t.priority == 'Medium')
                low_priority = sum(1 for t in tasks if t.priority == 'Low')
                
                workload_data.append({
                    "user_id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "total_tasks": len(tasks),
                    "high_priority": high_priority,
                    "medium_priority": medium_priority,
                    "low_priority": low_priority,
                    "workload_score": high_priority * 3 + medium_priority * 2 + low_priority
                })
            
            return sorted(workload_data, key=lambda x: x['workload_score'], reverse=True)
        except SQLAlchemyError as e:
            logger.error("Error getting team workload: %s", e)
            return {"error": str(e)}
    
    def search_tasks(self, query: str, project_id: Optional[int] = None) -> list:
        """Search tasks by title or description"""
        try:
            search_query = Task.query.filter(
                (Task.title.ilike(f"%{query}%")) | 
                (Task.description.ilike(f"%{query}%"))
            )
            
            if project_id:
                search_query = search_query.filter_by(project_id=project_id)
            
            tasks = search_query.all()
            
            return [{
                "id": t.id,
                "title": t.title,
                "description": t.description[:100] if t.description else None,
                "status": t.status,
                "priority": t.priority,
                "project_title": t.project.title if t.project else None
            } for t in tasks]
        except SQLAlchemyError as e:
            logger.error("Error searching tasks: %s", e)
            return {"error": str(e)}
    
    def get_dashboard_summary(self, user_id: int) -> dict:
        """Get a comprehensive dashboard summary for a user"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {"error": f"User {user_id} not found"}
            
            all_tasks = user.tasks
            pending_tasks = [t for t in all_tasks if t.status != 'Done']
            completed_today = [t for t in all_tasks if t.status == 'Done' and 
                             hasattr(t, 'updated_at') and 
                             t.updated_at.date() == datetime.utcnow().date()]
            overdue_tasks = [t for t in pending_tasks if t.due_date and 
                           t.due_date < datetime.utcnow().date()]
            
            return {
                "user_id": user.id,
                "username": user.username,
                "total_tasks": len(all_tasks),
                "pending_tasks": len(pending_tasks),
                "completed_tasks": sum(1 for t in all_tasks if t.status == 'Done'),
                "completed_today": len(completed_today),
                "overdue_tasks": len(overdue_tasks),
                "projects_count": len(user.projects),
                "high_priority_pending": sum(1 for t in pending_tasks if t.priority == 'High'),
                "upcoming_tasks_7_days": len([t for t in pending_tasks if t.due_date and 
                                            datetime.utcnow().date() <= t.due_date <= 
                                            datetime.utcnow().date() + timedelta(days=7)])
            }
        except SQLAlchemyError as e:
            logger.error("Error getting dashboard summary: %s", e)
            return {"error": str(e)}
    
    def handle_request(self, method: str, params: dict) -> Any:
        """Handle MCP requests"""
        handlers = {
            "get_projects": lambda: self.get_projects(params.get("user_id")),
            "get_project_details": lambda: self.get_project_details(params.get("project_id")),
            "get_tasks": lambda: self.get_tasks(
                params.get("project_id"),
                params.get("status"),
                params.get("user_id")
            ),
            "get_task_details": lambda: self.get_task_details(params.get("task_id")),
            "get_user_tasks": lambda: self.get_user_tasks(
                params.get("user_id"),
                params.get("status")
            ),
            "get_overdue_tasks": lambda: self.get_overdue_tasks(params.get("project_id")),
            "get_upcoming_tasks": lambda: self.get_upcoming_tasks(
                params.get("days", 7),
                params.get("project_id")
            ),
            "get_project_statistics": lambda: self.get_project_statistics(params.get("project_id")),
            "get_team_workload": lambda: self.get_team_workload(params.get("project_id")),
            "search_tasks": lambda: self.search_tasks(
                params.get("query"),
                params.get("project_id")
            ),
            "get_dashboard_summary": lambda: self.get_dashboard_summary(params.get("user_id"))
        }
        
        if method not in handlers:
            return {"error": f"Unknown method: {method}"}
        
        try:
            return handlers[method]()
        except Exception as e:
            logger.error("Error handling request %s: %s", method, e)
            return {"error": str(e)}

def main():
    """Main entry point for MCP server"""
    import sys
    
    server = TaskManagerMCPServer()
    
    # Read requests from stdin
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            method = request.get("method")
            params = request.get("params", {})
            
            result = server.handle_request(method, params)
            
            response = {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": result
            }
            print(json.dumps(response))
        except json.JSONDecodeError:
            print(json.dumps({
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": "Parse error"}
            }))
        except Exception as e:
            print(json.dumps({
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": str(e)}
            }))

if __name__ == "__main__":
    main()
