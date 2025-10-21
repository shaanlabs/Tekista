"""
Celery Configuration and Task Definitions
Handles background jobs for task assignment, performance tracking, and notifications
"""

from celery import Celery
from celery.schedules import crontab
from flask import current_app
import logging

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(__name__)

def make_celery(app):
    """Create Celery instance with Flask app context"""
    celery = Celery(
        app.import_name,
        backend=app.config.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
        broker=app.config.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    )
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

# ============================================================================
# TASK ASSIGNMENT JOBS
# ============================================================================

@celery_app.task(bind=True, max_retries=3)
def assign_next_task_for_user(self, user_id):
    """
    Automatically assign the next best task to a user after task completion
    
    Args:
        user_id: ID of the user who completed a task
    """
    try:
        from assignment import AssignmentService
        from models import User
        
        user = User.query.get(user_id)
        if not user:
            logger.error(f"User {user_id} not found")
            return {"success": False, "error": "User not found"}
        
        # Find next best task
        service = AssignmentService()
        recommendations = service.get_assignment_recommendations(
            task_id=None,
            organization_id=user.organization_id,
            top_n=1
        )
        
        if not recommendations:
            logger.info(f"No suitable tasks found for user {user_id}")
            return {"success": False, "message": "No suitable tasks available"}
        
        # Assign the best task
        best_task_data = recommendations[0]
        result = service.auto_assign_task(
            task_id=best_task_data['task_id'],
            organization_id=user.organization_id
        )
        
        if result:
            # Send notification
            send_task_assignment_notification.delay(
                user_id=user_id,
                task_id=result['task_id'],
                task_title=result.get('task_title', 'New Task'),
                skill_match=result['skill_match']
            )
            
            logger.info(f"Task {result['task_id']} assigned to user {user_id}")
            return {"success": True, "task_id": result['task_id']}
        else:
            logger.warning(f"Failed to assign task to user {user_id}")
            return {"success": False, "error": "Assignment failed"}
    
    except Exception as exc:
        logger.error(f"Error assigning task to user {user_id}: {str(exc)}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@celery_app.task
def find_and_assign_tasks_for_available_users(organization_id):
    """
    Find all available users and assign them suitable tasks
    
    Args:
        organization_id: ID of the organization
    """
    try:
        from assignment import AssignmentService
        from assignment.models import UserSkillProfile
        from models import User
        from enterprise.models import UserOrganizationRole
        
        # Get all available users
        users = User.query.join(
            UserOrganizationRole,
            User.id == UserOrganizationRole.user_id
        ).filter(
            UserOrganizationRole.organization_id == organization_id
        ).all()
        
        assigned_count = 0
        
        for user in users:
            # Check if user is available and has capacity
            profile = UserSkillProfile.query.filter_by(user_id=user.id).first()
            
            if not profile or not profile.is_available or profile.is_overloaded():
                continue
            
            # Try to assign a task
            result = assign_next_task_for_user.delay(user.id)
            if result:
                assigned_count += 1
        
        logger.info(f"Assigned tasks to {assigned_count} users in organization {organization_id}")
        return {"success": True, "assigned_count": assigned_count}
    
    except Exception as exc:
        logger.error(f"Error in find_and_assign_tasks_for_available_users: {str(exc)}")
        return {"success": False, "error": str(exc)}

# ============================================================================
# PERFORMANCE TRACKING JOBS
# ============================================================================

@celery_app.task(bind=True, max_retries=3)
def update_user_performance_metrics(self, user_id, assignment_id):
    """
    Update user's performance score based on task completion
    
    Args:
        user_id: ID of the user
        assignment_id: ID of the completed assignment
    """
    try:
        from assignment.models import TaskAssignment, AssignmentStatistics, UserSkillProfile
        from models import User
        
        user = User.query.get(user_id)
        assignment = TaskAssignment.query.get(assignment_id)
        
        if not user or not assignment:
            logger.error(f"User {user_id} or assignment {assignment_id} not found")
            return {"success": False, "error": "User or assignment not found"}
        
        # Get or create statistics
        stats = AssignmentStatistics.query.filter_by(user_id=user_id).first()
        if not stats:
            stats = AssignmentStatistics(user_id=user_id)
            from models import db
            db.session.add(stats)
        
        # Calculate performance score components
        estimation_accuracy = assignment.get_accuracy_ratio() if assignment.actual_completion_hours else 0.5
        on_time = 1.0 if assignment.completed_at <= assignment.task.due_date else 0.5
        skill_match = assignment.skill_match_score
        
        # Update performance score (weighted average)
        old_score = user.skill_profile.performance_score if user.skill_profile else 50.0
        new_score = (
            old_score * 0.6 +  # 60% weight to previous score
            estimation_accuracy * 20 +  # 20% weight to estimation accuracy
            on_time * 10 +  # 10% weight to on-time completion
            skill_match * 10  # 10% weight to skill match
        )
        
        # Update skill profile
        if user.skill_profile:
            user.skill_profile.performance_score = max(0, min(100, new_score))
            user.skill_profile.tasks_completed += 1
        
        # Update statistics
        stats.update_metrics()
        
        from models import db
        db.session.commit()
        
        logger.info(f"Updated performance metrics for user {user_id}: {old_score:.1f} → {new_score:.1f}")
        
        return {
            "success": True,
            "old_score": old_score,
            "new_score": new_score,
            "improvement": new_score - old_score
        }
    
    except Exception as exc:
        logger.error(f"Error updating performance metrics for user {user_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)

@celery_app.task
def recalculate_team_performance(organization_id):
    """
    Recalculate performance metrics for all users in an organization
    
    Args:
        organization_id: ID of the organization
    """
    try:
        from assignment.models import AssignmentStatistics
        from models import User
        from enterprise.models import UserOrganizationRole
        
        users = User.query.join(
            UserOrganizationRole,
            User.id == UserOrganizationRole.user_id
        ).filter(
            UserOrganizationRole.organization_id == organization_id
        ).all()
        
        updated_count = 0
        
        for user in users:
            stats = AssignmentStatistics.query.filter_by(user_id=user.id).first()
            if stats:
                stats.update_metrics()
                updated_count += 1
        
        from models import db
        db.session.commit()
        
        logger.info(f"Recalculated performance for {updated_count} users in organization {organization_id}")
        return {"success": True, "updated_count": updated_count}
    
    except Exception as exc:
        logger.error(f"Error recalculating team performance: {str(exc)}")
        return {"success": False, "error": str(exc)}

# ============================================================================
# NOTIFICATION JOBS
# ============================================================================

@celery_app.task
def send_task_assignment_notification(user_id, task_id, task_title, skill_match):
    """
    Send notification to user about new task assignment
    
    Args:
        user_id: ID of the user
        task_id: ID of the assigned task
        task_title: Title of the task
        skill_match: Skill match percentage
    """
    try:
        from models import User
        from notifications import send_notification
        
        user = User.query.get(user_id)
        if not user:
            logger.error(f"User {user_id} not found")
            return {"success": False, "error": "User not found"}
        
        # Create notification message
        message = f"🎯 New task assigned: {task_title} ({skill_match:.0%} skill match)"
        
        # Send in-app notification
        send_notification(
            user_id=user_id,
            title="New Task Assigned",
            message=message,
            notification_type="task_assignment",
            data={
                "task_id": task_id,
                "skill_match": skill_match
            }
        )
        
        logger.info(f"Notification sent to user {user_id} for task {task_id}")
        return {"success": True, "message": "Notification sent"}
    
    except Exception as exc:
        logger.error(f"Error sending notification to user {user_id}: {str(exc)}")
        return {"success": False, "error": str(exc)}

@celery_app.task
def send_performance_update_notification(user_id, old_score, new_score):
    """
    Send notification about performance score update
    
    Args:
        user_id: ID of the user
        old_score: Previous performance score
        new_score: New performance score
    """
    try:
        from models import User
        from notifications import send_notification
        
        user = User.query.get(user_id)
        if not user:
            return {"success": False, "error": "User not found"}
        
        improvement = new_score - old_score
        emoji = "📈" if improvement > 0 else "📉"
        
        message = f"{emoji} Performance score updated: {old_score:.1f} → {new_score:.1f}"
        
        send_notification(
            user_id=user_id,
            title="Performance Update",
            message=message,
            notification_type="performance_update",
            data={
                "old_score": old_score,
                "new_score": new_score,
                "improvement": improvement
            }
        )
        
        logger.info(f"Performance update notification sent to user {user_id}")
        return {"success": True}
    
    except Exception as exc:
        logger.error(f"Error sending performance update notification: {str(exc)}")
        return {"success": False, "error": str(exc)}

# ============================================================================
# SCHEDULED TASKS
# ============================================================================

@celery_app.task
def cleanup_old_assignments():
    """
    Clean up old completed assignments (older than 90 days)
    """
    try:
        from assignment.models import TaskAssignment
        from datetime import datetime, timedelta
        from models import db
        
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        deleted_count = TaskAssignment.query.filter(
            TaskAssignment.assignment_status == 'completed',
            TaskAssignment.completed_at < cutoff_date
        ).delete()
        
        db.session.commit()
        
        logger.info(f"Cleaned up {deleted_count} old assignments")
        return {"success": True, "deleted_count": deleted_count}
    
    except Exception as exc:
        logger.error(f"Error cleaning up old assignments: {str(exc)}")
        return {"success": False, "error": str(exc)}

@celery_app.task
def generate_daily_performance_reports():
    """
    Generate daily performance reports for all organizations
    """
    try:
        from enterprise.models import Organization
        
        organizations = Organization.query.all()
        
        for org in organizations:
            recalculate_team_performance.delay(org.id)
        
        logger.info(f"Generated performance reports for {len(organizations)} organizations")
        return {"success": True, "org_count": len(organizations)}
    
    except Exception as exc:
        logger.error(f"Error generating performance reports: {str(exc)}")
        return {"success": False, "error": str(exc)}

# ============================================================================
# CELERY BEAT SCHEDULE
# ============================================================================

celery_app.conf.beat_schedule = {
    'cleanup-old-assignments': {
        'task': 'celery_app.cleanup_old_assignments',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    'generate-daily-reports': {
        'task': 'celery_app.generate_daily_performance_reports',
        'schedule': crontab(hour=8, minute=0),  # Daily at 8 AM
    },
    'find-and-assign-tasks': {
        'task': 'celery_app.find_and_assign_tasks_for_available_users',
        'schedule': crontab(minute=0),  # Every hour
        'args': (1,),  # Default organization ID
    },
}

celery_app.conf.timezone = 'UTC'
