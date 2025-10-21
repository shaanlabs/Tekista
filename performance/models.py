"""
Performance Tracking Models
Stores performance metrics and analytics data
"""

from datetime import datetime
from models import db
from sqlalchemy import Index

# ============================================================================
# PERFORMANCE LOG
# ============================================================================

class PerformanceLog(db.Model):
    """Performance metrics log for analytics and tracking"""
    __tablename__ = "performance_log"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey('task_assignment.id'))
    
    # Completion metrics
    tasks_completed = db.Column(db.Integer, default=0)
    on_time_ratio = db.Column(db.Float, default=0.0)  # 0-1
    
    # Skill metrics
    skill_accuracy = db.Column(db.Float, default=0.0)  # 0-1
    
    # Difficulty metrics
    difficulty_factor = db.Column(db.Float, default=0.0)  # 0-1
    
    # Time metrics
    avg_completion_time = db.Column(db.Float, default=0.0)  # hours
    avg_completion_speed = db.Column(db.Float, default=0.0)  # days early/late
    
    # Performance score
    performance_score = db.Column(db.Float, default=0.0)  # 0-100
    score_change = db.Column(db.Float, default=0.0)  # Change from previous
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = db.relationship('User', backref='performance_logs')
    assignment = db.relationship('TaskAssignment', backref='performance_logs')
    
    __table_args__ = (
        Index('idx_performance_log_user_id', 'user_id'),
        Index('idx_performance_log_created_at', 'created_at'),
        Index('idx_performance_log_user_created', 'user_id', 'created_at'),
    )
    
    def __repr__(self):
        return f'<PerformanceLog user={self.user_id} score={self.performance_score:.1f}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'assignment_id': self.assignment_id,
            'tasks_completed': self.tasks_completed,
            'on_time_ratio': self.on_time_ratio,
            'skill_accuracy': self.skill_accuracy,
            'difficulty_factor': self.difficulty_factor,
            'avg_completion_time': self.avg_completion_time,
            'avg_completion_speed': self.avg_completion_speed,
            'performance_score': self.performance_score,
            'score_change': self.score_change,
            'created_at': self.created_at.isoformat()
        }

# ============================================================================
# PERFORMANCE MILESTONE
# ============================================================================

class PerformanceMilestone(db.Model):
    """Track performance milestones and achievements"""
    __tablename__ = "performance_milestone"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Milestone type
    milestone_type = db.Column(db.String(100), nullable=False)  # e.g., "100_tasks", "perfect_week"
    milestone_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    
    # Achievement details
    achieved_value = db.Column(db.Float)  # e.g., 100 for 100_tasks
    achievement_data = db.Column(db.JSON)  # Additional data
    
    # Metadata
    achieved_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='performance_milestones')
    
    __table_args__ = (
        Index('idx_performance_milestone_user_id', 'user_id'),
        Index('idx_performance_milestone_type', 'milestone_type'),
    )
    
    def __repr__(self):
        return f'<PerformanceMilestone {self.milestone_name}>'

# ============================================================================
# PERFORMANCE BADGE
# ============================================================================

class PerformanceBadge(db.Model):
    """Badges earned by users based on performance"""
    __tablename__ = "performance_badge"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Badge details
    badge_name = db.Column(db.String(100), nullable=False)
    badge_description = db.Column(db.Text)
    badge_icon = db.Column(db.String(255))  # URL or emoji
    
    # Badge criteria
    criteria = db.Column(db.String(100))  # e.g., "score_above_90"
    criteria_value = db.Column(db.Float)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Metadata
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='performance_badges')
    
    __table_args__ = (
        Index('idx_performance_badge_user_id', 'user_id'),
    )
    
    def __repr__(self):
        return f'<PerformanceBadge {self.badge_name}>'

# ============================================================================
# PERFORMANCE SNAPSHOT
# ============================================================================

class PerformanceSnapshot(db.Model):
    """Daily performance snapshot for trend analysis"""
    __tablename__ = "performance_snapshot"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Snapshot date
    snapshot_date = db.Column(db.Date, nullable=False, index=True)
    
    # Daily metrics
    tasks_completed_today = db.Column(db.Integer, default=0)
    cumulative_tasks = db.Column(db.Integer, default=0)
    daily_on_time_ratio = db.Column(db.Float, default=0.0)
    cumulative_on_time_ratio = db.Column(db.Float, default=0.0)
    
    # Daily performance
    daily_performance_score = db.Column(db.Float, default=0.0)
    cumulative_performance_score = db.Column(db.Float, default=0.0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='performance_snapshots')
    
    __table_args__ = (
        Index('idx_performance_snapshot_user_id', 'user_id'),
        Index('idx_performance_snapshot_date', 'snapshot_date'),
        Index('idx_performance_snapshot_user_date', 'user_id', 'snapshot_date'),
    )
    
    def __repr__(self):
        return f'<PerformanceSnapshot {self.user_id} {self.snapshot_date}>'

# ============================================================================
# PERFORMANCE COMPARISON
# ============================================================================

class PerformanceComparison(db.Model):
    """Compare performance between users and teams"""
    __tablename__ = "performance_comparison"
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Comparison entities
    user_id_1 = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user_id_2 = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Comparison metrics
    score_difference = db.Column(db.Float)
    on_time_difference = db.Column(db.Float)
    skill_accuracy_difference = db.Column(db.Float)
    
    # Comparison result
    winner_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Metadata
    compared_at = db.Column(db.DateTime, default=datetime.utcnow)
    period_days = db.Column(db.Integer, default=30)
    
    # Relationships
    user_1 = db.relationship('User', foreign_keys=[user_id_1])
    user_2 = db.relationship('User', foreign_keys=[user_id_2])
    winner = db.relationship('User', foreign_keys=[winner_user_id])
    
    __table_args__ = (
        Index('idx_performance_comparison_users', 'user_id_1', 'user_id_2'),
    )
    
    def __repr__(self):
        return f'<PerformanceComparison {self.user_id_1} vs {self.user_id_2}>'
