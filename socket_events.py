"""
Socket.IO Events for Real-Time Notifications
Handles real-time notification delivery via WebSockets
"""

import logging

from flask import request
from flask_login import current_user
from flask_socketio import SocketIO, emit, join_room, leave_room

from models import User, db
from notifications_service import NotificationEvents, NotificationService

logger = logging.getLogger(__name__)

# Store active user connections
active_users = {}

def init_socketio(app):
    """Initialize Socket.IO"""
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='threading',
        ping_timeout=60,
        ping_interval=25
    )
    
    @socketio.on('connect')
    def handle_connect():
        """Handle user connection"""
        if current_user.is_authenticated:
            user_id = current_user.id
            active_users[user_id] = request.sid
            
            # Join user-specific room
            join_room(f'user_{user_id}')
            
            # Get unread count
            unread_count = NotificationService.get_unread_count(user_id)
            
            logger.info("User %s connected. Unread: %s", user_id, unread_count)
            
            # Emit connection confirmation
            emit('connected', {
                'user_id': user_id,
                'unread_count': unread_count
            })
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle user disconnection"""
        if current_user.is_authenticated:
            user_id = current_user.id
            if user_id in active_users:
                del active_users[user_id]
            
            leave_room(f'user_{user_id}')
            logger.info("User %s disconnected", user_id)
    
    @socketio.on('mark_notification_read')
    def handle_mark_read(data):
        """Mark notification as read"""
        notification_id = data.get('notification_id')
        
        if not notification_id:
            emit('error', {'message': 'notification_id required'})
            return
        
        success = NotificationService.mark_as_read(notification_id)
        
        if success:
            unread_count = NotificationService.get_unread_count(current_user.id)
            emit('notification_marked_read', {
                'notification_id': notification_id,
                'unread_count': unread_count
            })
    
    @socketio.on('mark_all_read')
    def handle_mark_all_read():
        """Mark all notifications as read"""
        count = NotificationService.mark_all_as_read(current_user.id)
        
        emit('all_notifications_marked_read', {
            'marked_count': count,
            'unread_count': 0
        })
    
    @socketio.on('request_unread_count')
    def handle_unread_count_request():
        """Get current unread count"""
        unread_count = NotificationService.get_unread_count(current_user.id)
        
        emit('unread_count_update', {
            'unread_count': unread_count
        })
    
    return socketio

# ============================================================================
# NOTIFICATION EMISSION FUNCTIONS
# ============================================================================

def emit_notification(user_id: int, notification_data: dict):
    """
    Emit notification to user via Socket.IO
    
    Args:
        user_id: ID of the user
        notification_data: Notification data to emit
    """
    try:
        from flask import current_app
        
        socketio = current_app.extensions.get('socketio')
        if not socketio:
            logger.warning("Socket.IO not initialized")
            return
        
        socketio.emit(
            'new_notification',
            notification_data,
            room=f'user_{user_id}'
        )
        
        logger.info("Emitted notification to user %s", user_id)
    
    except Exception as exc:
        logger.error("Error emitting notification: %s", exc)

def emit_task_assigned(user_id: int, task_id: int, task_title: str, assigned_by_id: int):
    """Emit task assignment notification"""
    notification = NotificationEvents.task_assigned(
        user_id,
        task_id,
        task_title,
        assigned_by_id
    )
    
    if notification:
        emit_notification(user_id, {
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'type': 'task_assigned',
            'task_id': task_id,
            'action_url': notification.action_url,
            'created_at': notification.created_at.isoformat()
        })

def emit_task_completed(user_id: int, task_id: int, task_title: str, completed_by_id: int):
    """Emit task completion notification"""
    notification = NotificationEvents.task_completed(
        user_id,
        task_id,
        task_title,
        completed_by_id
    )
    
    if notification:
        emit_notification(user_id, {
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'type': 'task_completed',
            'task_id': task_id,
            'action_url': notification.action_url,
            'created_at': notification.created_at.isoformat()
        })

def emit_performance_update(user_id: int, new_score: float, old_score: float):
    """Emit performance update notification"""
    notification = NotificationEvents.performance_update(
        user_id,
        new_score,
        old_score
    )
    
    if notification:
        emit_notification(user_id, {
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'type': 'performance_update',
            'data': notification.data,
            'created_at': notification.created_at.isoformat()
        })

def broadcast_unread_count_update(user_id: int):
    """Broadcast unread count update to user"""
    try:
        from flask import current_app
        
        socketio = current_app.extensions.get('socketio')
        if not socketio:
            return
        
        unread_count = NotificationService.get_unread_count(user_id)
        
        socketio.emit(
            'unread_count_update',
            {'unread_count': unread_count},
            room=f'user_{user_id}'
        )
    
    except Exception as exc:
        logger.error("Error broadcasting unread count: %s", exc)
