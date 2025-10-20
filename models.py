import secrets
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager

# project_users = db.Table(
# 	'project_users',
# 	db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
# 	db.Column('project_id', db.Integer, db.ForeignKey('project.id'))
# )

# task_assignees = db.Table(
# 	'task_assignees',
# 	db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
# 	db.Column('task_id', db.Integer, db.ForeignKey('task.id'))
# )

# task_dependencies = db.Table(
# 	'task_dependencies',
# 	db.Column('predecessor_id', db.Integer, db.ForeignKey('task.id')),
# 	db.Column('successor_id', db.Integer, db.ForeignKey('task.id'))
# )

# class User(UserMixin, db.Model):
# 	__tablename__ = "user"
# 	id = db.Column(db.Integer, primary_key=True)
# 	username = db.Column(db.String(80), unique=True, nullable=False)
# 	email = db.Column(db.String(120), unique=True, nullable=False)
# 	password_hash = db.Column(db.String(128), nullable=False)
# 	# API token
# 	api_token = db.Column(db.String(128), unique=True, index=True, nullable=True)
# 	token_expiration = db.Column(db.DateTime, nullable=True)

# 	# relationships
# 	projects = db.relationship('Project', secondary=project_users, back_populates='users')
# 	tasks = db.relationship('Task', secondary=task_assignees, back_populates='tasks')

# 	def set_password(self, password):
# 		self.password_hash = generate_password_hash(password)

# 	def check_password(self, password):
# 		return check_password_hash(self.password_hash, password)

# 	def get_api_token(self, expires_in=3600):
# 		"""Generate or return existing token if still valid."""
# 		now = datetime.utcnow()
# 		if self.api_token and self.token_expiration and self.token_expiration > now + timedelta(seconds=60):
# 			return self.api_token
# 		self.api_token = secrets.token_urlsafe(32)
# 		self.token_expiration = now + timedelta(seconds=expires_in)
# 		db.session.add(self)
# 		db.session.commit()
# 		return self.api_token

# 	def revoke_api_token(self):
# 		self.api_token = None
# 		self.token_expiration = None
# 		db.session.add(self)
# 		db.session.commit()

# 	@staticmethod
# 	def verify_api_token(token):
# 		if not token:
# 			return None
# 		u = User.query.filter_by(api_token=token).first()
# 		if u is None:
# 			return None
# 		if u.token_expiration and u.token_expiration < datetime.utcnow():
# 			# expired
# 			return None
# 		return u

# 	@login_manager.user_loader
# 	def load_user(user_id):
# 		return User.query.get(int(user_id))

# class Project(db.Model):
# 	__tablename__ = "project"
# 	id = db.Column(db.Integer, primary_key=True)
# 	title = db.Column(db.String(150), nullable=False)
# 	description = db.Column(db.Text)
# 	deadline = db.Column(db.Date)
# 	created_at = db.Column(db.DateTime, default=datetime.utcnow)
# 	users = db.relationship('User', secondary=project_users, back_populates='projects')
# 	tasks = db.relationship('Task', back_populates='project', cascade='all, delete-orphan')

# 	def progress(self):
# 		total = len(self.tasks)
# 		if total == 0:
# 			return 0
# 		done = sum(1 for t in self.tasks if t.status == 'Done')
# 		return int((done / total) * 100)

# class Task(db.Model):
# 	__tablename__ = "task"
# 	id = db.Column(db.Integer, primary_key=True)
# 	title = db.Column(db.String(150), nullable=False)
# 	description = db.Column(db.Text)
# 	due_date = db.Column(db.Date)
# 	priority = db.Column(db.String(20), default='Normal')  # Low, Normal, High
# 	status = db.Column(db.String(30), default='To Do')  # To Do, In Progress, Done
# 	project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
# 	project = db.relationship('Project', back_populates='tasks')
# 	assignees = db.relationship('User', secondary=task_assignees, back_populates='tasks')
# 	# dependencies
# 	predecessors = db.relationship(
# 		'Task',
# 		secondary=task_dependencies,
# 		primaryjoin=id==task_dependencies.c.successor_id,
# 		secondaryjoin=id==task_dependencies.c.predecessor_id,
# 		backref='successors'
# 	)
# 	comments = db.relationship('Comment', back_populates='task', cascade='all, delete-orphan')

# 	def can_start(self):
# 		# task can start if all predecessors are done
# 		return all(p.status == 'Done' for p in self.predecessors)

# class Comment(db.Model):
# 	__tablename__ = "comment"
# 	id = db.Column(db.Integer, primary_key=True)
# 	body = db.Column(db.Text, nullable=False)
# 	author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
# 	task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
# 	created_at = db.Column(db.DateTime, default=datetime.utcnow)
# 	author = db.relationship('User')
# 	task = db.relationship('Task', back_populates='comments')
# ... [imports and table definitions unchanged] ...
# changed from here
# class User(UserMixin, db.Model):
#     __tablename__ = "user"
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(80), unique=True, nullable=False)
#     email = db.Column(db.String(120), unique=True, nullable=False)
#     password_hash = db.Column(db.String(128), nullable=False)
#     api_token = db.Column(db.String(128), unique=True, index=True, nullable=True)
#     token_expiration = db.Column(db.DateTime, nullable=True)

#     # relationships
#     projects = db.relationship('Project', secondary=project_users, back_populates='users')
#     # 🔧 FIXED: back_populates points to 'assignees' in Task
#     tasks = db.relationship('Task', secondary=task_assignees, back_populates='assignees')

#     def set_password(self, password):
#         self.password_hash = generate_password_hash(password)

#     def check_password(self, password):
#         return check_password_hash(self.password_hash, password)

#     def get_api_token(self, expires_in=3600):
#         now = datetime.utcnow()
#         if self.api_token and self.token_expiration and self.token_expiration > now + timedelta(seconds=60):
#             return self.api_token
#         self.api_token = secrets.token_urlsafe(32)
#         self.token_expiration = now + timedelta(seconds=expires_in)
#         db.session.add(self)
#         db.session.commit()
#         return self.api_token
import secrets
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager

# ✅ Define association tables FIRST — at top level
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

# ✅ NOW define models — they can safely reference the tables above
class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    api_token = db.Column(db.String(128), unique=True, index=True, nullable=True)
    token_expiration = db.Column(db.DateTime, nullable=True)

    # relationships — now 'project_users' and 'task_assignees' exist!
    projects = db.relationship('Project', secondary=project_users, back_populates='users')
    tasks = db.relationship('Task', secondary=task_assignees, back_populates='assignees')

    # ... rest of your methods ...
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

# 🔻 Move user_loader OUTSIDE the class
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Project(db.Model):
    __tablename__ = "project"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    deadline = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    users = db.relationship('User', secondary=project_users, back_populates='projects')
    tasks = db.relationship('Task', back_populates='project', cascade='all, delete-orphan')

    def progress(self):
        total = len(self.tasks)
        if total == 0:
            return 0
        done = sum(1 for t in self.tasks if t.status == 'Done')
        return int((done / total) * 100)


class Task(db.Model):
    __tablename__ = "task"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.Date)
    priority = db.Column(db.String(20), default='Normal')
    status = db.Column(db.String(30), default='To Do')
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    project = db.relationship('Project', back_populates='tasks')
    # 🔧 This is correct: back_populates='tasks' refers to User.tasks
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
        return all(p.status == 'Done' for p in self.predecessors)


class Comment(db.Model):
    __tablename__ = "comment"
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author = db.relationship('User')
    task = db.relationship('Task', back_populates='comments')