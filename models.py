import secrets
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Define association tables FIRST — at top level
project_users = db.Table(
    'project_users',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'))
)

task_assignees = db.Table(
    'task_assignees',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('task_id', db.Integer, db.ForeignKey('task.id'))
)

task_dependencies = db.Table(
    'task_dependencies',
    db.Column('predecessor_id', db.Integer, db.ForeignKey('task.id')),
    db.Column('successor_id', db.Integer, db.ForeignKey('task.id'))
)

# Define models — they can safely reference the tables above
class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    # Optional enterprise fields (FKs declared as strings to avoid import cycles)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=True)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=True)
    custom_role_id = db.Column(db.Integer, db.ForeignKey('custom_role.id'), nullable=True)
    api_token = db.Column(db.String(128), unique=True, index=True, nullable=True)
    token_expiration = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # scheduling fields
    current_workload = db.Column(db.Float, default=0.0)  # 0..100
    availability = db.Column(db.String(20), default='Available')  # Available|Busy|In a Meeting|On a Break|Out of Office
    # rbac relationship
    role = db.relationship('Role')

    # relationships — now 'project_users' and 'task_assignees' exist!
    projects = db.relationship('Project', secondary=project_users, back_populates='users')
    tasks = db.relationship('Task', secondary=task_assignees, back_populates='assignees')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_api_token(self, expires_in=3600):
        """Generate or return existing token if still valid."""
        now = datetime.utcnow()
        if self.api_token and self.token_expiration and self.token_expiration > now + timedelta(seconds=60):
            return self.api_token
        self.api_token = secrets.token_urlsafe(32)
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        db.session.commit()
        return self.api_token

    def revoke_api_token(self):
        self.api_token = None
        self.token_expiration = None
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def verify_api_token(token):
        if not token:
            return None
        u = User.query.filter_by(api_token=token).first()
        if u is None or (u.token_expiration and u.token_expiration < datetime.utcnow()):
            return None
        return u

    def __repr__(self):
        return f'<User {self.username}>'


# ========= Anomaly Engine Core =========

class UserBehaviorBaseline(db.Model):
    __tablename__ = 'user_behavior_baseline'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    metric_key = db.Column(db.String(120), index=True)
    center = db.Column(db.Float)
    spread = db.Column(db.Float)
    seasonality_json = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)


class UserDailyFeature(db.Model):
    __tablename__ = 'user_daily_feature'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    date = db.Column(db.Date, index=True)
    feature_key = db.Column(db.String(120), index=True)
    value = db.Column(db.Float)
    source = db.Column(db.String(40))


class AnomalyEvent(db.Model):
    __tablename__ = 'anomaly_event'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    severity = db.Column(db.String(20))  # low|medium|high
    type = db.Column(db.String(80))
    occurred_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    source_event_id = db.Column(db.Integer, nullable=True)
    evidence_json = db.Column(db.Text)
    explanation_json = db.Column(db.Text)
    resolved = db.Column(db.Boolean, default=False)
    resolved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)


class UserReliabilityScore(db.Model):
    __tablename__ = 'user_reliability_score'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    score = db.Column(db.Float, default=100.0)
    computed_at = db.Column(db.DateTime, default=datetime.utcnow)


class Role(db.Model):
    __tablename__ = "role"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Role {self.name}>'


class CustomRole(db.Model):
    __tablename__ = "custom_role"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<CustomRole {self.name}>'


class AuditLog(db.Model):
    __tablename__ = "audit_log"
    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(80), nullable=False)
    target_type = db.Column(db.String(80))
    target_id = db.Column(db.Integer)
    meta = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    actor = db.relationship('User')

    def __repr__(self):
        return f'<AuditLog {self.action} #{self.id}>'


class UserProfile(db.Model):
    __tablename__ = 'user_profile'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, index=True)
    job_title = db.Column(db.String(120), nullable=True)
    department = db.Column(db.String(120), nullable=True)
    interests = db.Column(db.Text, nullable=True)
    skills_json = db.Column(db.Text, nullable=True)  # current skills snapshot for UI tags
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class Organization(db.Model):
    __tablename__ = 'organization'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Organization {self.name}>'


class Project(db.Model):
    __tablename__ = "project"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    deadline = db.Column(db.Date)
    # Optional enterprise field to associate projects with organizations
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    users = db.relationship('User', secondary=project_users, back_populates='projects')
    tasks = db.relationship('Task', back_populates='project', cascade='all, delete-orphan')

    def progress(self):
        total = len(self.tasks)
        if total == 0:
            return 0
        done = sum(1 for t in self.tasks if t.status == 'Completed')
        return int((done / total) * 100)

    def __repr__(self):
        return f'<Project {self.title}>'


class Task(db.Model):
    __tablename__ = "task"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.Date)
    priority = db.Column(db.String(20), default='Normal')  # Critical, High, Normal, Low
    estimated_hours = db.Column(db.Float, default=4.0)
    status = db.Column(db.String(30), default='To Do')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Subtasks
    parent_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=True)
    subtasks = db.relationship('Task', backref=db.backref('parent', remote_side=[id]))
    # Recurrence (RFC-style rule or simple text)
    recurrence_rule = db.Column(db.String(200), nullable=True)
    recurrence_end = db.Column(db.Date, nullable=True)
    # Templates
    is_template = db.Column(db.Boolean, default=False)
    template_name = db.Column(db.String(120), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    project = db.relationship('Project', back_populates='tasks')
    # This is correct: back_populates='tasks' refers to User.tasks
    assignees = db.relationship('User', secondary=task_assignees, back_populates='tasks')
    
    predecessors = db.relationship(
        'Task',
        secondary=task_dependencies,
        primaryjoin=id==task_dependencies.c.successor_id,
        secondaryjoin=id==task_dependencies.c.predecessor_id,
        backref='successors'
    )
    comments = db.relationship('Comment', back_populates='task', cascade='all, delete-orphan')

    def can_start(self):
        return all(p.status == 'Completed' for p in self.predecessors)

    def __repr__(self):
        return f'<Task {self.title}>'


class Comment(db.Model):
    __tablename__ = "comment"
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author = db.relationship('User')
    task = db.relationship('Task', back_populates='comments')

    def __repr__(self):
        return f'<Comment {self.id}>'


# ========= Advanced Phase Scaffolding (minimal, safe) =========

class Setting(db.Model):
    __tablename__ = 'setting'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(120), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)


class UserCalendarToken(db.Model):
    __tablename__ = 'user_calendar_token'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    provider = db.Column(db.String(30))  # google|outlook
    token_encrypted = db.Column(db.Text)
    refresh_encrypted = db.Column(db.Text)
    scope = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)


class UserCapacity(db.Model):
    __tablename__ = 'user_capacity'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date = db.Column(db.Date, index=True)
    blocked_hours = db.Column(db.Float, default=0.0)
    capacity_hours = db.Column(db.Float, default=8.0)
    source = db.Column(db.String(40))  # calendar|manual
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class TaskOutcome(db.Model):
    __tablename__ = 'task_outcome'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    estimate_vs_actual = db.Column(db.Float, nullable=True)
    qa_first_pass = db.Column(db.Boolean, default=None)
    reassignments = db.Column(db.Integer, default=0)
    overdue_flag = db.Column(db.Boolean, default=None)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)


class UserSkillHistory(db.Model):
    __tablename__ = 'user_skill_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    skill = db.Column(db.String(80))
    delta = db.Column(db.Float)
    reason = db.Column(db.String(200))
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)


class WorkflowTemplate(db.Model):
    __tablename__ = 'workflow_template'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class WorkflowStep(db.Model):
    __tablename__ = 'workflow_step'
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('workflow_template.id'))
    step_order = db.Column(db.Integer, default=0)
    title = db.Column(db.String(150), nullable=False)
    required_roles = db.Column(db.String(200))
    required_skills = db.Column(db.String(200))
    default_estimated_hours = db.Column(db.Float, default=4.0)


class EpicDemand(db.Model):
    __tablename__ = 'epic_demand'
    id = db.Column(db.Integer, primary_key=True)
    epic_id = db.Column(db.Integer, nullable=False)
    role = db.Column(db.String(80))
    seniority = db.Column(db.String(40))
    count = db.Column(db.Integer, default=1)


class UserBurnoutMetric(db.Model):
    __tablename__ = 'user_burnout_metric'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    time_in_critical_days = db.Column(db.Integer, default=0)
    context_switch_7d = db.Column(db.Integer, default=0)
    critical_tasks_active = db.Column(db.Integer, default=0)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)


class ProjectHealth(db.Model):
    __tablename__ = 'project_health'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    health_score = db.Column(db.Float, default=0.0)
    risk_score = db.Column(db.Float, default=0.0)
    computed_at = db.Column(db.DateTime, default=datetime.utcnow)


class BudgetForecast(db.Model):
    __tablename__ = 'budget_forecast'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    burn_rate = db.Column(db.Float, default=0.0)
    forecast_overrun_pct = db.Column(db.Float, default=0.0)
    computed_at = db.Column(db.DateTime, default=datetime.utcnow)


class AutomationRule(db.Model):
    __tablename__ = 'automation_rule'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    trigger_json = db.Column(db.Text)  # JSON
    action_json = db.Column(db.Text)   # JSON
    enabled = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AutomationRun(db.Model):
    __tablename__ = 'automation_run'
    id = db.Column(db.Integer, primary_key=True)
    rule_id = db.Column(db.Integer, db.ForeignKey('automation_rule.id'))
    status = db.Column(db.String(40), default='pending')
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)
    meta = db.Column(db.Text)


class ProcessEvent(db.Model):
    __tablename__ = 'process_event'
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(80))
    entity = db.Column(db.String(40))
    entity_id = db.Column(db.Integer)
    event_type = db.Column(db.String(80))
    at = db.Column(db.DateTime, default=datetime.utcnow)
    meta = db.Column(db.Text)


class AIAgentJob(db.Model):
    __tablename__ = 'ai_agent_job'
    id = db.Column(db.Integer, primary_key=True)
    job_type = db.Column(db.String(80))  # decompose|apply_plan|summary
    payload_json = db.Column(db.Text)
    status = db.Column(db.String(40), default='queued')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)


class AIAuditLog(db.Model):
    __tablename__ = 'ai_audit_log'
    id = db.Column(db.Integer, primary_key=True)
    actor = db.Column(db.String(80))  # AI-Agent-01
    action = db.Column(db.String(120))
    target_type = db.Column(db.String(80))
    target_id = db.Column(db.Integer)
    meta = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)