from flask import current_app, has_app_context
try:
    import openai
except ImportError:
    openai = None
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from models import db, Task, Project, User, Comment
try:
    import numpy as np
    from sklearn.linear_model import LinearRegression
except ImportError:
    np = None
    LinearRegression = None
from collections import defaultdict
import json

class AIAssistant:
    def __init__(self, openai_api_key=None):
        # Do not touch current_app here; may be constructed outside app context
        self.openai_api_key = openai_api_key

    def estimate_task_duration(self, task_title, task_description, project_id=None):
        """
        Estimate task duration based on similar historical tasks
        """
        # Get historical tasks for this project or all projects
        query = Task.query
        if project_id:
            query = query.filter_by(project_id=project_id)
        
        # Get completed tasks with actual durations (if tracking)
        historical_tasks = query.filter(
            Task.status == 'Done',
            Task.due_date.isnot(None)
        ).all()
        
        if not historical_tasks:
            return None  # Not enough data
            
        # Simple average for now (can be enhanced with ML model)
        durations = []
        for t in historical_tasks:
            if t.due_date and t.created_at:
                duration = (t.due_date - t.created_at.date()).days
                if duration > 0:
                    durations.append(duration)
        
        return round(sum(durations) / len(durations), 1) if durations else 3  # Default to 3 days

    def predict_deadline_risks(self, project_id=None):
        """
        Predict which tasks are at risk of missing their deadlines
        """
        query = Task.query
        if project_id:
            query = query.filter_by(project_id=project_id)
            
        tasks = query.filter(
            Task.status != 'Done',
            Task.due_date.isnot(None)
        ).all()
        
        today = datetime.utcnow().date()
        at_risk = []
        
        for task in tasks:
            # Simple risk calculation based on days remaining vs historical completion
            if task.due_date and task.created_at:
                total_days = (task.due_date - task.created_at.date()).days
                days_elapsed = (today - task.created_at.date()).days
                
                if days_elapsed > 0 and total_days > 0:
                    completion_rate = task.progress / 100  # Assuming progress is tracked
                    expected_completion_days = days_elapsed / (completion_rate + 0.0001)  # Avoid division by zero
                    risk_score = min(100, max(0, (1 - (task.due_date - today).days / expected_completion_days) * 100))
                    
                    if risk_score > 70:  # High risk threshold
                        at_risk.append({
                            'task': task,
                            'risk_score': round(risk_score),
                            'days_remaining': (task.due_date - today).days
                        })
        
        return sorted(at_risk, key=lambda x: x['risk_score'], reverse=True)

    def generate_ai_summary(self, project_id=None):
        """
        Generate a natural language summary of project status
        """
        # Resolve API key at call time to avoid app context issues
        api_key = self.openai_api_key
        if not api_key and has_app_context():
            api_key = current_app.config.get('OPENAI_API_KEY')
        if not api_key:
            return "AI features require an OpenAI API key to be configured."
        try:
            openai.api_key = api_key
        except Exception:
            pass
            
        query = Project.query
        if project_id:
            query = query.filter_by(id=project_id)
            
        projects = query.all()
        if not projects:
            return "No projects found."
            
        summary = ""
        for project in projects:
            completed = sum(1 for t in project.tasks if t.status == 'Done')
            total = len(project.tasks)
            progress = (completed / total * 100) if total > 0 else 0
            
            # Get recent activity
            recent_tasks = Task.query.filter_by(project_id=project.id)\
                                  .order_by(Task.due_date.desc())\
                                  .limit(3).all()
            
            summary += f"Project: {project.title}\n"
            summary += f"Progress: {progress:.1f}% ({completed}/{total} tasks completed)\n"
            
            if recent_tasks:
                summary += "Recent tasks:\n"
                for task in recent_tasks:
                    status = "✅" if task.status == 'Done' else "⏳" if task.status == 'In Progress' else "📝"
                    summary += f"- {status} {task.title} (Due: {task.due_date})\n"
            
            # Add deadline risk assessment
            at_risk = self.predict_deadline_risks(project.id)
            if at_risk:
                summary += "\n⚠️ Tasks at risk of missing deadlines:\n"
                for risk in at_risk[:3]:  # Show top 3
                    summary += f"- {risk['task'].title} ({risk['risk_score']}% risk, {risk['days_remaining']} days left)\n"
            
            summary += "\n" + "-"*50 + "\n\n"
        
        return summary

    def process_natural_language_task(self, text, project_id=None, user_id=None):
        """
        Parse natural language input to create a task
        Example: "Remind me to finalize UI by Friday"
        """
        api_key = self.openai_api_key
        if not api_key and has_app_context():
            api_key = current_app.config.get('OPENAI_API_KEY')
        if not api_key:
            return {"error": "AI features require an OpenAI API key to be configured."}
        try:
            openai.api_key = api_key
        except Exception:
            pass
            
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a task parsing assistant. Extract task details from natural language input and return in JSON format with keys: 'title', 'due_date' (YYYY-MM-DD or null), 'priority' (High/Medium/Low), and 'description' (or null)."},
                    {"role": "user", "content": text}
                ]
            )
            
            # Parse the response
            import json
            try:
                task_data = json.loads(response.choices[0].message['content'])
                
                # Create the task
                task = Task(
                    title=task_data.get('title', 'New Task'),
                    description=task_data.get('description', ''),
                    due_date=datetime.strptime(task_data['due_date'], '%Y-%m-%d').date() if task_data.get('due_date') else None,
                    priority=task_data.get('priority', 'Medium'),
                    status='To Do',
                    project_id=project_id
                )
                
                # Assign to user if specified
                if user_id:
                    user = User.query.get(user_id)
                    if user:
                        task.assignees.append(user)
                
                db.session.add(task)
                db.session.commit()
                
                return {"success": True, "task_id": task.id}
                
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                return {"error": f"Failed to parse AI response: {str(e)}"}
                
        except Exception as e:
            return {"error": f"AI processing error: {str(e)}"}

    def analyze_workload_balance(self, project_id=None):
        """
        Analyze and suggest workload balance across team members
        """
        query = Task.query.filter(Task.status != 'Done')
        if project_id:
            query = query.filter_by(project_id=project_id)
            
        tasks = query.all()
        
        # Count tasks per user
        user_tasks = defaultdict(list)
        for task in tasks:
            for user in task.assignees:
                user_tasks[user.id].append(task)
        
        # Calculate workload metrics
        workload_data = []
        for user_id, tasks in user_tasks.items():
            user = User.query.get(user_id)
            if not user:
                continue
                
            high_priority = sum(1 for t in tasks if t.priority == 'High')
            medium_priority = sum(1 for t in tasks if t.priority == 'Medium')
            low_priority = sum(1 for t in tasks if t.priority == 'Low')
            
            workload_data.append({
                'user_id': user.id,
                'username': user.username,
                'total_tasks': len(tasks),
                'high_priority': high_priority,
                'medium_priority': medium_priority,
                'low_priority': low_priority,
                'workload_score': high_priority * 3 + medium_priority * 2 + low_priority
            })
        
        # Sort by workload score (descending)
        workload_data.sort(key=lambda x: x['workload_score'], reverse=True)
        
        return workload_data

    def get_ai_suggestions(self, user_id=None):
        """
        Get personalized AI suggestions for a user
        """
        api_key = self.openai_api_key
        if not api_key and has_app_context():
            api_key = current_app.config.get('OPENAI_API_KEY')
        if not api_key:
            return []
        try:
            openai.api_key = api_key
        except Exception:
            pass
            
        user = User.query.get(user_id) if user_id else None
        if not user:
            return []
            
        # Get user's tasks
        tasks = Task.query.join(
            task_assignees, Task.id == task_assignees.c.task_id
        ).filter(
            task_assignees.c.user_id == user.id,
            Task.status != 'Done'
        ).all()
        
        # Get project context
        projects = {p.id: p for p in Project.query.join(project_users).filter(project_users.c.user_id == user.id).all()}
        
        # Prepare context for AI
        context = f"User: {user.username}\n"
        context += f"Current time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n\n"
        
        context += "=== Current Tasks ===\n"
        for task in tasks[:5]:  # Limit to 5 most relevant tasks
            project_name = projects.get(task.project_id, Project(title='Unknown')).title
            context += f"- {task.title} (Project: {project_name}, Priority: {task.priority}, Due: {task.due_date})\n"
        
        # Add recent activity
        recent_comments = Comment.query.filter_by(author_id=user.id).order_by(Comment.created_at.desc()).limit(3).all()
        if recent_comments:
            context += "\n=== Recent Activity ===\n"
            for comment in recent_comments:
                context += f"- Commented on '{comment.task.title}': {comment.body[:50]}...\n"
        
        # Get AI suggestions
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful productivity assistant. Provide 3-5 concise, actionable suggestions to help the user manage their workload more effectively. Focus on prioritization, time management, and workload balance. Format as a bulleted list."},
                    {"role": "user", "content": context}
                ],
                max_tokens=300
            )
            
            return response.choices[0].message['content'].split('\n')
            
        except Exception as e:
            current_app.logger.error(f"AI suggestion error: {str(e)}")
            return []

# Create a singleton instance
ai_assistant = AIAssistant()
