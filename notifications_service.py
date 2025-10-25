"""
Notifications Service
Handles notification creation, delivery, and management
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from models import db
from notifications_models import (Notification, NotificationPreference,
                                  NotificationTemplate)

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for managing notifications"""
    
    @staticmethod
    def create_notification(
        user_id: int,
        title: str,
        message: str,
        notification_type: str,
        task_id: Optional[int] = None,
        project_id: Optional[int] = None,
        related_user_id: Optional[int] = None,
        data: Optional[Dict] = None,
        action_url: Optional[str] = None
    ) -> Optional[Notification]:
        """
        Create a new notification
        
        Args:
            user_id: ID of the user receiving notification
            title: Notification title
            message: Notification message
            notification_type: Type of notification (task_assigned, task_completed, etc.)
            task_id: Related task ID (optional)
            project_id: Related project ID (optional)
            related_user_id: User who triggered the notification (optional)
            data: Additional data (optional)
            action_url: URL to navigate to (optional)
            
        Returns:
            Created Notification object or None
        """
        try:
            # Check user preferences
            prefs = NotificationPreference.query.filter_by(user_id=user_id).first()
            
            if prefs:
                # Check if this notification type is enabled
                pref_key = f'{notification_type}'
                if hasattr(prefs, pref_key) and not getattr(prefs, pref_key):
                    logger.info(f"Notification type {notification_type} disabled for user {user_id}")
                    return None
            
            # Create notification
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                task_id=task_id,
                project_id=project_id,
                related_user_id=related_user_id,
                data=data,
                action_url=action_url
            )
            
            db.session.add(notification)
            db.session.commit()
            
            logger.info(f"Created notification {notification.id} for user {user_id}")
            return notification
        
        except Exception as exc:
            logger.error(f"Error creating notification: {str(exc)}")
            return None
    
    @staticmethod
    def create_from_template(
        user_id: int,
        template_key: str,
        notification_type: str,
        template_vars: Dict,
        task_id: Optional[int] = None,
        project_id: Optional[int] = None,
        related_user_id: Optional[int] = None,
        action_url: Optional[str] = None
    ) -> Optional[Notification]:
        """
        Create notification from template
        
        Args:
            user_id: ID of the user
            template_key: Template key
            notification_type: Notification type
            template_vars: Variables for template rendering
            task_id: Related task ID (optional)
            project_id: Related project ID (optional)
            related_user_id: Related user ID (optional)
            action_url: Action URL (optional)
            
        Returns:
            Created Notification or None
        """
        try:
            template = NotificationTemplate.get_template(template_key)
            
            if not template:
                logger.warning(f"Template {template_key} not found")
                return None
            
            title, message = template.render(**template_vars)
            
            return NotificationService.create_notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                task_id=task_id,
                project_id=project_id,
                related_user_id=related_user_id,
                data=template_vars,
                action_url=action_url
            )
        
        except Exception as exc:
            logger.error(f"Error creating notification from template: {str(exc)}")
            return None
    
    @staticmethod
    def get_user_notifications(
        user_id: int,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Notification]:
        """
        Get notifications for a user
        
        Args:
            user_id: ID of the user
            unread_only: Only return unread notifications
            limit: Maximum number of notifications
            
        Returns:
            List of Notification objects
        """
        try:
            query = Notification.query.filter_by(user_id=user_id)
            
            if unread_only:
                query = query.filter_by(is_read=False)
            
            notifications = query.order_by(
                Notification.created_at.desc()
            ).limit(limit).all()
            
            return notifications
        
        except Exception as exc:
            logger.error(f"Error getting notifications for user {user_id}: {str(exc)}")
            return []
    
    @staticmethod
    def get_unread_count(user_id: int) -> int:
        """Get count of unread notifications"""
        try:
            count = Notification.query.filter_by(
                user_id=user_id,
                is_read=False
            ).count()
            return count
        except Exception as exc:
            logger.error(f"Error getting unread count for user {user_id}: {str(exc)}")
            return 0
    
    @staticmethod
    def mark_as_read(notification_id: int) -> bool:
        """Mark notification as read"""
        try:
            notification = Notification.query.get(notification_id)
            if notification:
                notification.mark_as_read()
                return True
            return False
        except Exception as exc:
            logger.error(f"Error marking notification as read: {str(exc)}")
            return False
    
    @staticmethod
    def mark_all_as_read(user_id: int) -> int:
        """Mark all notifications as read for user"""
        try:
            count = Notification.query.filter_by(
                user_id=user_id,
                is_read=False
            ).update({'is_read': True, 'read_at': datetime.utcnow()})
            
            db.session.commit()
            return count
        except Exception as exc:
            logger.error(f"Error marking all notifications as read: {str(exc)}")
            return 0
    
    @staticmethod
    def delete_notification(notification_id: int) -> bool:
        """Delete a notification"""
        try:
            notification = Notification.query.get(notification_id)
            if notification:
                db.session.delete(notification)
                db.session.commit()
                return True
            return False
        except Exception as exc:
            logger.error(f"Error deleting notification: {str(exc)}")
            return False
    
    @staticmethod
    def cleanup_old_notifications(days: int = 30) -> int:
        """Delete notifications older than N days"""
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            count = Notification.query.filter(
                Notification.created_at < cutoff_date
            ).delete()
            
            db.session.commit()
            logger.info(f"Cleaned up {count} old notifications")
            return count
        except Exception as exc:
            logger.error(f"Error cleaning up old notifications: {str(exc)}")
            return 0
    
    @staticmethod
    def get_or_create_preferences(user_id: int) -> NotificationPreference:
        """Get or create notification preferences for user"""
        try:
            prefs = NotificationPreference.query.filter_by(user_id=user_id).first()
            
            if not prefs:
                prefs = NotificationPreference(user_id=user_id)
                db.session.add(prefs)
                db.session.commit()
            
            return prefs
        except Exception as exc:
            logger.error(f"Error getting/creating preferences: {str(exc)}")
            return None
    
    @staticmethod
    def update_preferences(user_id: int, **kwargs) -> bool:
        """Update notification preferences"""
        try:
            prefs = NotificationService.get_or_create_preferences(user_id)
            
            if not prefs:
                return False
            
            for key, value in kwargs.items():
                if hasattr(prefs, key):
                    setattr(prefs, key, value)
            
            db.session.commit()
            return True
        except Exception as exc:
            logger.error(f"Error updating preferences: {str(exc)}")
            return False

# ============================================================================
# NOTIFICATION EVENTS
# ============================================================================

class NotificationEvents:
    """Predefined notification events"""
    
    @staticmethod
    def task_assigned(user_id: int, task_id: int, task_title: str, assigned_by_id: int) -> Optional[Notification]:
        """Notify user about task assignment"""
        from models import User
        
        assigned_by = User.query.get(assigned_by_id)
        assigned_by_name = assigned_by.username if assigned_by else "System"
        
        return NotificationService.create_notification(
            user_id=user_id,
            title="📋 New Task Assigned",
            message=f"{assigned_by_name} assigned you: {task_title}",
            notification_type="task_assigned",
            task_id=task_id,
            related_user_id=assigned_by_id,
            action_url=f"/tasks/{task_id}"
        )
    
    @staticmethod
    def task_completed(user_id: int, task_id: int, task_title: str, completed_by_id: int) -> Optional[Notification]:
        """Notify user about task completion"""
        from models import User
        
        completed_by = User.query.get(completed_by_id)
        completed_by_name = completed_by.username if completed_by else "System"
        
        return NotificationService.create_notification(
            user_id=user_id,
            title="✅ Task Completed",
            message=f"{completed_by_name} completed: {task_title}",
            notification_type="task_completed",
            task_id=task_id,
            related_user_id=completed_by_id,
            action_url=f"/tasks/{task_id}"
        )
    
    @staticmethod
    def task_overdue(user_id: int, task_id: int, task_title: str) -> Optional[Notification]:
        """Notify user about overdue task"""
        return NotificationService.create_notification(
            user_id=user_id,
            title="⚠️ Task Overdue",
            message=f"Task is overdue: {task_title}",
            notification_type="task_overdue",
            task_id=task_id,
            action_url=f"/tasks/{task_id}"
        )
    
    @staticmethod
    def performance_update(user_id: int, new_score: float, old_score: float) -> Optional[Notification]:
        """Notify user about performance update"""
        change = new_score - old_score
        emoji = "📈" if change > 0 else "📉"
        
        return NotificationService.create_notification(
            user_id=user_id,
            title=f"{emoji} Performance Update",
            message=f"Your performance score updated: {old_score:.1f} → {new_score:.1f}",
            notification_type="performance_update",
            data={'old_score': old_score, 'new_score': new_score}
        )
    
    @staticmethod
    def comment_added(user_id: int, task_id: int, commenter_id: int, comment_text: str) -> Optional[Notification]:
        """Notify user about comment on task"""
        from models import User
        
        commenter = User.query.get(commenter_id)
        commenter_name = commenter.username if commenter else "Someone"
        
        return NotificationService.create_notification(
            user_id=user_id,
            title="💬 New Comment",
            message=f"{commenter_name} commented: {comment_text[:50]}...",
            notification_type="comment_added",
            task_id=task_id,
            related_user_id=commenter_id,
            action_url=f"/tasks/{task_id}"
        )
