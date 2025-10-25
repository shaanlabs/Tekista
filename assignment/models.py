"""
Task Assignment Models
Stores user skill profiles and task assignment history
"""

from datetime import datetime

from sqlalchemy import Index
from sqlalchemy.dialects.postgresql import JSON

from models import db

# ============================================================================
# USER SKILL PROFILE
# ============================================================================


class UserSkillProfile(db.Model):
    """User skill profile for task assignment"""

    __tablename__ = "user_skill_profile"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True
    )

    # Skills and experience
    skills = db.Column(JSON, default=[])  # List of skills
    experience_level = db.Column(db.Integer, default=1)  # 1-10 scale

    # Performance metrics
    performance_score = db.Column(db.Float, default=50.0)  # 0-100 scale
    tasks_completed = db.Column(db.Integer, default=0)
    avg_completion_time = db.Column(db.Float, default=8.0)  # hours

    # Current workload
    current_workload_hours = db.Column(db.Float, default=0.0)

    # Availability
    max_weekly_hours = db.Column(db.Float, default=40.0)
    is_available = db.Column(db.Boolean, default=True)

    # Preferences
    preferred_difficulty_min = db.Column(db.Integer, default=1)
    preferred_difficulty_max = db.Column(db.Integer, default=10)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user = db.relationship("User", backref="skill_profile")

    __table_args__ = (Index("idx_user_skill_profile_user_id", "user_id"),)

    def __repr__(self):
        return f"<UserSkillProfile {self.user_id}>"

    def add_skill(self, skill: str):
        """Add a skill to user's profile"""
        if not self.skills:
            self.skills = []

        skill_lower = skill.lower()
        if skill_lower not in [s.lower() for s in self.skills]:
            self.skills.append(skill)
            db.session.commit()

    def remove_skill(self, skill: str):
        """Remove a skill from user's profile"""
        if self.skills:
            self.skills = [s for s in self.skills if s.lower() != skill.lower()]
            db.session.commit()

    def update_performance_score(self, new_score: float):
        """Update performance score"""
        self.performance_score = max(0, min(100, new_score))
        db.session.commit()

    def update_workload(self, hours: float):
        """Update current workload"""
        self.current_workload_hours = max(0, hours)
        db.session.commit()

    def is_overloaded(self) -> bool:
        """Check if user is overloaded"""
        return self.current_workload_hours >= self.max_weekly_hours

    def available_capacity(self) -> float:
        """Get available capacity in hours"""
        return max(0, self.max_weekly_hours - self.current_workload_hours)


# ============================================================================
# TASK ASSIGNMENT RECORD
# ============================================================================


class TaskAssignment(db.Model):
    """Record of task assignments"""

    __tablename__ = "task_assignment"

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("task.id"), nullable=False)
    assigned_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    assigned_by_id = db.Column(
        db.Integer, db.ForeignKey("user.id")
    )  # NULL for auto-assignment

    # Assignment strategy and scores
    assignment_strategy = db.Column(
        db.String(50)
    )  # skill_match, workload_balance, performance, hybrid
    skill_match_score = db.Column(db.Float, default=0.0)  # 0-1
    workload_score = db.Column(db.Float, default=0.0)  # 0-1
    performance_score = db.Column(db.Float, default=0.0)  # 0-1
    overall_score = db.Column(db.Float, default=0.0)  # 0-1

    # Estimated metrics
    estimated_completion_hours = db.Column(db.Float)
    actual_completion_hours = db.Column(db.Float)

    # Assignment details
    assignment_reason = db.Column(db.Text)  # Human-readable reason
    notes = db.Column(db.Text)

    # Reassignment tracking
    reassigned_at = db.Column(db.DateTime)
    reassignment_reason = db.Column(db.Text)

    # Status
    assignment_status = db.Column(
        db.String(50), default="active"
    )  # active, completed, cancelled

    # Timestamps
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    # Relationships
    task = db.relationship("Task", backref="assignments")
    assigned_user = db.relationship(
        "User", foreign_keys=[assigned_user_id], backref="task_assignments"
    )
    assigned_by = db.relationship("User", foreign_keys=[assigned_by_id])

    __table_args__ = (
        Index("idx_task_assignment_task_id", "task_id"),
        Index("idx_task_assignment_user_id", "assigned_user_id"),
        Index("idx_task_assignment_assigned_at", "assigned_at"),
    )

    def __repr__(self):
        return f"<TaskAssignment task={self.task_id} user={self.assigned_user_id}>"

    def mark_completed(self, actual_hours: float = None):
        """Mark assignment as completed"""
        self.assignment_status = "completed"
        self.completed_at = datetime.utcnow()

        if actual_hours:
            self.actual_completion_hours = actual_hours

        db.session.commit()

    def cancel(self, reason: str = None):
        """Cancel assignment"""
        self.assignment_status = "cancelled"
        self.reassignment_reason = reason
        db.session.commit()

    def get_accuracy_ratio(self) -> float:
        """Get accuracy of time estimation"""
        if not self.actual_completion_hours or not self.estimated_completion_hours:
            return 0.0

        ratio = self.actual_completion_hours / self.estimated_completion_hours

        # Return accuracy (1.0 = perfect, 0.0 = completely wrong)
        if ratio <= 1.0:
            return ratio
        else:
            return 1.0 / ratio


# ============================================================================
# SKILL ENDORSEMENT
# ============================================================================


class SkillEndorsement(db.Model):
    """Peer endorsement of skills"""

    __tablename__ = "skill_endorsement"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    endorsed_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    skill = db.Column(db.String(100), nullable=False)
    endorsement_level = db.Column(db.Integer, default=1)  # 1-5 scale

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship(
        "User", foreign_keys=[user_id], backref="skill_endorsements_received"
    )
    endorsed_by = db.relationship("User", foreign_keys=[endorsed_by_id])

    __table_args__ = (
        Index("idx_skill_endorsement_user_id", "user_id"),
        Index("idx_skill_endorsement_skill", "skill"),
        db.UniqueConstraint(
            "user_id", "endorsed_by_id", "skill", name="unique_endorsement"
        ),
    )

    def __repr__(self):
        return f"<SkillEndorsement {self.user_id} - {self.skill}>"


# ============================================================================
# ASSIGNMENT FEEDBACK
# ============================================================================


class AssignmentFeedback(db.Model):
    """Feedback on task assignments for continuous improvement"""

    __tablename__ = "assignment_feedback"

    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(
        db.Integer, db.ForeignKey("task_assignment.id"), nullable=False
    )

    # Feedback scores
    difficulty_rating = db.Column(db.Integer)  # 1-5 scale
    skill_match_rating = db.Column(db.Integer)  # 1-5 scale
    workload_rating = db.Column(db.Integer)  # 1-5 scale

    # Comments
    comments = db.Column(db.Text)

    # Suggestions
    suggestions = db.Column(db.Text)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    assignment = db.relationship("TaskAssignment", backref="feedback")

    __table_args__ = (Index("idx_assignment_feedback_assignment_id", "assignment_id"),)

    def __repr__(self):
        return f"<AssignmentFeedback assignment={self.assignment_id}>"


# ============================================================================
# ASSIGNMENT STATISTICS
# ============================================================================


class AssignmentStatistics(db.Model):
    """Aggregated statistics for assignment quality"""

    __tablename__ = "assignment_statistics"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Assignment quality metrics
    total_assignments = db.Column(db.Integer, default=0)
    completed_assignments = db.Column(db.Integer, default=0)
    cancelled_assignments = db.Column(db.Integer, default=0)

    # Time estimation accuracy
    avg_estimation_accuracy = db.Column(db.Float, default=0.0)  # 0-1

    # Skill match quality
    avg_skill_match_score = db.Column(db.Float, default=0.0)  # 0-1

    # Performance trends
    avg_difficulty_assigned = db.Column(db.Float, default=0.0)  # 1-10
    avg_completion_time = db.Column(db.Float, default=0.0)  # hours

    # Workload balance
    avg_workload_utilization = db.Column(db.Float, default=0.0)  # 0-1

    # Feedback scores
    avg_difficulty_rating = db.Column(db.Float, default=0.0)  # 1-5
    avg_skill_match_rating = db.Column(db.Float, default=0.0)  # 1-5
    avg_workload_rating = db.Column(db.Float, default=0.0)  # 1-5

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user = db.relationship("User", backref="assignment_statistics")

    __table_args__ = (Index("idx_assignment_statistics_user_id", "user_id"),)

    def __repr__(self):
        return f"<AssignmentStatistics {self.user_id}>"

    def update_metrics(self):
        """Recalculate all metrics from assignments"""

        assignments = TaskAssignment.query.filter_by(
            assigned_user_id=self.user_id
        ).all()

        if not assignments:
            return

        self.total_assignments = len(assignments)
        self.completed_assignments = sum(
            1 for a in assignments if a.assignment_status == "completed"
        )
        self.cancelled_assignments = sum(
            1 for a in assignments if a.assignment_status == "cancelled"
        )

        # Calculate average metrics
        completed = [a for a in assignments if a.assignment_status == "completed"]

        if completed:
            self.avg_skill_match_score = sum(
                a.skill_match_score for a in completed
            ) / len(completed)
            self.avg_completion_time = sum(
                a.actual_completion_hours or 0 for a in completed
            ) / len(completed)

            # Accuracy
            accurate = [
                a
                for a in completed
                if a.actual_completion_hours and a.estimated_completion_hours
            ]
            if accurate:
                self.avg_estimation_accuracy = sum(
                    a.get_accuracy_ratio() for a in accurate
                ) / len(accurate)

        db.session.commit()
