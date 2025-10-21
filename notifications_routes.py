"""
Notifications API Routes
Provides endpoints for notification management
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db
from notifications_models import Notification, NotificationPreference
from notifications_service import NotificationService
import logging

logger = logging.getLogger(__name__)

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

# ============================================================================
# NOTIFICATION ENDPOINTS
# ============================================================================

@notifications_bp.route('', methods=['GET'])
@login_required
def get_notifications():
    """
    Get notifications for current user
    
    Query Parameters:
        unread_only: Only return unread (default: false)
        limit: Maximum number (default: 50)
        page: Page number (default: 1)
        per_page: Items per page (default: 20)
    """
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    limit = request.args.get('limit', 50, type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Notification.query.filter_by(user_id=current_user.id)
    
    if unread_only:
        query = query.filter_by(is_read=False)
    
    notifications = query.order_by(
        Notification.created_at.desc()
    ).paginate(page=page, per_page=per_page)
    
    return jsonify({
        'total': notifications.total,
        'pages': notifications.pages,
        'current_page': page,
        'notifications': [n.to_dict() for n in notifications.items]
    }), 200

@notifications_bp.route('/unread-count', methods=['GET'])
@login_required
def get_unread_count():
    """Get count of unread notifications"""
    count = NotificationService.get_unread_count(current_user.id)
    
    return jsonify({
        'user_id': current_user.id,
        'unread_count': count
    }), 200

@notifications_bp.route('/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_as_read(notification_id):
    """Mark notification as read"""
    notification = Notification.query.get_or_404(notification_id)
    
    # Check authorization
    if notification.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    notification.mark_as_read()
    
    return jsonify({
        'success': True,
        'notification_id': notification_id,
        'is_read': True
    }), 200

@notifications_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_as_read():
    """Mark all notifications as read"""
    count = NotificationService.mark_all_as_read(current_user.id)
    
    return jsonify({
        'success': True,
        'marked_count': count
    }), 200

@notifications_bp.route('/<int:notification_id>', methods=['DELETE'])
@login_required
def delete_notification(notification_id):
    """Delete a notification"""
    notification = Notification.query.get_or_404(notification_id)
    
    # Check authorization
    if notification.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    success = NotificationService.delete_notification(notification_id)
    
    if success:
        return jsonify({'success': True}), 200
    else:
        return jsonify({'error': 'Failed to delete'}), 500

# ============================================================================
# NOTIFICATION PREFERENCES ENDPOINTS
# ============================================================================

@notifications_bp.route('/preferences', methods=['GET'])
@login_required
def get_preferences():
    """Get notification preferences for current user"""
    prefs = NotificationService.get_or_create_preferences(current_user.id)
    
    if not prefs:
        return jsonify({'error': 'Failed to get preferences'}), 500
    
    return jsonify(prefs.to_dict()), 200

@notifications_bp.route('/preferences', methods=['PUT'])
@login_required
def update_preferences():
    """Update notification preferences"""
    data = request.get_json()
    
    success = NotificationService.update_preferences(current_user.id, **data)
    
    if success:
        prefs = NotificationService.get_or_create_preferences(current_user.id)
        return jsonify({
            'success': True,
            'preferences': prefs.to_dict()
        }), 200
    else:
        return jsonify({'error': 'Failed to update preferences'}), 500

# ============================================================================
# NOTIFICATION STATISTICS ENDPOINTS
# ============================================================================

@notifications_bp.route('/statistics', methods=['GET'])
@login_required
def get_notification_statistics():
    """Get notification statistics for current user"""
    total = Notification.query.filter_by(user_id=current_user.id).count()
    unread = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    
    # Count by type
    types = db.session.query(
        Notification.notification_type,
        db.func.count(Notification.id)
    ).filter_by(user_id=current_user.id).group_by(
        Notification.notification_type
    ).all()
    
    type_counts = {t[0]: t[1] for t in types}
    
    return jsonify({
        'user_id': current_user.id,
        'total_notifications': total,
        'unread_notifications': unread,
        'read_notifications': total - unread,
        'by_type': type_counts
    }), 200

# ============================================================================
# NOTIFICATION SEARCH ENDPOINTS
# ============================================================================

@notifications_bp.route('/search', methods=['GET'])
@login_required
def search_notifications():
    """
    Search notifications
    
    Query Parameters:
        q: Search query
        type: Notification type filter
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
    """
    query_str = request.args.get('q', '')
    notification_type = request.args.get('type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Notification.query.filter_by(user_id=current_user.id)
    
    if query_str:
        query = query.filter(
            db.or_(
                Notification.title.ilike(f'%{query_str}%'),
                Notification.message.ilike(f'%{query_str}%')
            )
        )
    
    if notification_type:
        query = query.filter_by(notification_type=notification_type)
    
    if start_date:
        from datetime import datetime
        start = datetime.fromisoformat(start_date)
        query = query.filter(Notification.created_at >= start)
    
    if end_date:
        from datetime import datetime
        end = datetime.fromisoformat(end_date)
        query = query.filter(Notification.created_at <= end)
    
    notifications = query.order_by(
        Notification.created_at.desc()
    ).limit(50).all()
    
    return jsonify({
        'query': query_str,
        'results': len(notifications),
        'notifications': [n.to_dict() for n in notifications]
    }), 200
