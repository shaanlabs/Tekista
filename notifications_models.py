"""
Notification Models
Stores and manages user notifications
"""

from datetime import datetime
from models import db
from sqlalchemy import Index

# ============================================================================
# NOTIFICATION
# ============================================================================

class Notification(db.Model):
    """User notification model"""
    __tablename__ = "notification"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Notification content
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # task_assigned, task_completed, etc.
    
    # Related data
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    related_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Who triggered the notification
    
    # Status
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    
    # Additional data
    data = db.Column(db.JSON)  # Additional context data
    action_url = db.Column(db.String(500))  # URL to navigate to
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='notifications')
    task = db.relationship('Task', backref='notifications')
    project = db.relationship('Project', backref='notifications')
    related_user = db.relationship('User', foreign_keys=[related_user_id])
    
    __table_args__ = (
        Index('idx_notification_user_id', 'user_id'),
        Index('idx_notification_is_read', 'is_read'),
        Index('idx_notification_created_at', 'created_at'),
        Index('idx_notification_user_read', 'user_id', 'is_read'),
    )
    
    def __repr__(self):
        return f'<Notification {self.id} user={self.user_id}>'
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'task_id': self.task_id,
            'project_id': self.project_id,
            'related_user_id': self.related_user_id,
            'related_user_name': self.related_user.username if self.related_user else None,
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'data': self.data,
            'action_url': self.action_url,
            'created_at': self.created_at.isoformat()
        }

# ============================================================================
# NOTIFICATION PREFERENCE
# ============================================================================

class NotificationPreference(db.Model):
    """User notification preferences"""
    __tablename__ = "notification_preference"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    
    # Notification type preferences
    task_assigned = db.Column(db.Boolean, default=True)
    task_completed = db.Column(db.Boolean, default=True)
    task_overdue = db.Column(db.Boolean, default=True)
    comment_added = db.Column(db.Boolean, default=True)
    team_update = db.Column(db.Boolean, default=True)
    performance_update = db.Column(db.Boolean, default=True)
    
    # Delivery preferences
    email_notifications = db.Column(db.Boolean, default=False)
    push_notifications = db.Column(db.Boolean, default=True)
    in_app_notifications = db.Column(db.Boolean, default=True)
    
    # Quiet hours
    quiet_hours_enabled = db.Column(db.Boolean, default=False)
    quiet_hours_start = db.Column(db.String(5))  # HH:MM format
    quiet_hours_end = db.Column(db.String(5))    # HH:MM format
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='notification_preference')
    
    def __repr__(self):
        return f'<NotificationPreference {self.user_id}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'user_id': self.user_id,
            'task_assigned': self.task_assigned,
            'task_completed': self.task_completed,
            'task_overdue': self.task_overdue,
            'comment_added': self.comment_added,
            'team_update': self.team_update,
            'performance_update': self.performance_update,
            'email_notifications': self.email_notifications,
            'push_notifications': self.push_notifications,
            'in_app_notifications': self.in_app_notifications,
            'quiet_hours_enabled': self.quiet_hours_enabled,
            'quiet_hours_start': self.quiet_hours_start,
            'quiet_hours_end': self.quiet_hours_end
        }

# ============================================================================
# NOTIFICATION TEMPLATE
# ============================================================================

class NotificationTemplate(db.Model):
    """Notification message templates"""
    __tablename__ = "notification_template"
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Template details
    template_key = db.Column(db.String(100), nullable=False, unique=True)
    title_template = db.Column(db.String(255), nullable=False)
    message_template = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)
    
    # Template variables (for documentation)
    variables = db.Column(db.JSON)  # e.g., {user_name, task_title, project_name}
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<NotificationTemplate {self.template_key}>'
    
    @staticmethod
    def get_template(template_key):
        """Get template by key"""
        return NotificationTemplate.query.filter_by(template_key=template_key).first()
    
    def render(self, **kwargs):
        """Render template with variables"""
        title = self.title_template
        message = self.message_template
        
        for key, value in kwargs.items():
            title = title.replace(f'{{{key}}}', str(value))
            message = message.replace(f'{{{key}}}', str(value))
        
        return title, message
