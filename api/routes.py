from flask import jsonify, request, url_for, g, Response
from flask_login import login_required
from datetime import datetime, timedelta
from sqlalchemy import func
from . import api_bp
from models import Project, Task, User
from app import db
from .auth import api_auth_required

def task_to_dict(t):
	return {
		'id': t.id,
		'title': t.title,
		'description': t.description,
		'status': t.status,
		'priority': t.priority,
		'due_date': str(t.due_date) if t.due_date else None,
		'assignees': [{'id': u.id, 'username': u.username} for u in t.assignees],
		'project_id': t.project_id
	}

def project_to_dict(p):
	return {
		'id': p.id,
		'title': p.title,
		'description': p.description,
		'deadline': str(p.deadline) if p.deadline else None,
		'progress': p.progress(),
		'tasks': [task_to_dict(t) for t in p.tasks]
	}

@api_bp.route('/projects', methods=['GET'])
@api_auth_required
def api_projects():
	projects = Project.query.all()
	return jsonify([project_to_dict(p) for p in projects])

@api_bp.route('/projects/<int:project_id>', methods=['GET'])
@api_auth_required
def api_project_detail(project_id):
	p = Project.query.get_or_404(project_id)
	return jsonify(project_to_dict(p))

@api_bp.route('/tasks', methods=['GET', 'POST'])
@api_auth_required
def api_tasks():
	if request.method == 'GET':
		tasks = Task.query.all()
		return jsonify([task_to_dict(t) for t in tasks])
	data = request.get_json() or {}
	# expected fields: title, project_id, assignees (list of user ids), due_date(optional), priority
	title = data.get('title')
	project_id = data.get('project_id')
	if not title or not project_id:
		return jsonify({'error':'title and project_id required'}), 400
	project = Project.query.get_or_404(project_id)
	t = Task(title=title, description=data.get('description'), priority=data.get('priority','Normal'), project=project)
	# set assignees
	for uid in data.get('assignees', []):
		u = User.query.get(uid)
		if u:
			t.assignees.append(u)
	db.session.add(t); db.session.commit()
	return jsonify(task_to_dict(t)), 201, {'Location': url_for('api.api_tasks')}

@api_bp.route('/tasks/<int:task_id>', methods=['GET'])
@api_auth_required
def api_task_detail(task_id):
	t = Task.query.get_or_404(task_id)
	return jsonify(task_to_dict(t))

# New token endpoints
@api_bp.route('/token', methods=['POST'])
def api_get_token():
	"""
	Accepts JSON { "username": "...", "password": "..." } and returns { "token": "...", "expires_in": seconds }.
	"""
	data = request.get_json() or {}
	username = data.get('username')
	password = data.get('password')
	if not username or not password:
		return jsonify({'error':'username and password required'}), 400
	user = User.query.filter_by(username=username).first()
	if user is None or not user.check_password(password):
		return jsonify({'error':'invalid credentials'}), 401
	token = user.get_api_token(expires_in=3600)
	return jsonify({'token': token, 'expires_in': 3600})

@api_bp.route('/token/revoke', methods=['POST'])
@api_auth_required
def api_revoke_token():
	"""
	Revoke token for the authenticated API user (token or session).
	"""
	user = g.get('api_user')
	if not user:
		return jsonify({'error':'unauthorized'}), 401
	user.revoke_api_token()
	return jsonify({'status':'token revoked'})

# Advanced Enterprise API Endpoints
@api_bp.route('/analytics/metrics', methods=['GET'])
@api_auth_required
def api_analytics_metrics():
	"""Get dashboard analytics metrics."""
	from models import Project, Task, User
	
	# Calculate metrics (guard against null due_date)
	total_projects = Project.query.count()
	total_tasks = Task.query.count()
	completed_tasks = Task.query.filter_by(status='Done').count()
	overdue_tasks = Task.query.filter(
		Task.due_date != None,  # noqa: E711
		Task.due_date < datetime.now().date(),
		Task.status != 'Done'
	).count()
	# Simple productivity metric (avoid relying on non-existent created_at)
	recent_completed = completed_tasks
	
	return jsonify({
		'projects': total_projects,
		'tasks': total_tasks,
		'completed': completed_tasks,
		'overdue': overdue_tasks,
		'productivity': round((recent_completed / max(total_tasks, 1)) * 100, 1)
	})

@api_bp.route('/analytics/performance', methods=['GET'])
@api_auth_required
def api_analytics_performance():
	"""Get performance analytics data."""
	from models import Task
	from sqlalchemy import func

	# Attempt to group by due_date if present; otherwise return aggregate only
	days = request.args.get('days', 30, type=int)
	start_date = datetime.now().date() - timedelta(days=days)

	try:
		performance_data = db.session.query(
			func.date(Task.due_date).label('date'),
			func.count(Task.id).label('total'),
			func.sum(func.case([(Task.status == 'Done', 1)], else_=0)).label('completed')
		).filter(
			Task.due_date != None,  # noqa: E711
			Task.due_date >= start_date
		).group_by(func.date(Task.due_date)).all()

		return jsonify([{
			'date': str(row.date),
			'total': row.total,
			'completed': row.completed or 0
		} for row in performance_data])
	except Exception:
		total = Task.query.count()
		completed = Task.query.filter_by(status='Done').count()
		return jsonify([{
			'date': str(datetime.now().date()),
			'total': total,
			'completed': completed
		}])

@api_bp.route('/search', methods=['GET'])
@api_auth_required
def api_search():
	"""Advanced search functionality."""
	query = request.args.get('q', '')
	if len(query) < 2:
		return jsonify([])
	
	from models import Project, Task, User
	
	results = []
	
	# Search projects
	projects = Project.query.filter(
		Project.title.contains(query) | Project.description.contains(query)
	).limit(5).all()
	
	for project in projects:
		results.append({
			'type': 'project',
			'id': project.id,
			'title': project.title,
			'description': project.description,
			'url': f'/projects/{project.id}'
		})
	
	# Search tasks
	tasks = Task.query.filter(
		Task.title.contains(query) | Task.description.contains(query)
	).limit(5).all()
	
	for task in tasks:
		results.append({
			'type': 'task',
			'id': task.id,
			'title': task.title,
			'description': task.description,
			'status': task.status,
			'url': f'/tasks/{task.id}'
		})
	
	# Search users
	users = User.query.filter(
		User.username.contains(query) | User.email.contains(query)
	).limit(5).all()
	
	for user in users:
		results.append({
			'type': 'user',
			'id': user.id,
			'title': user.username,
			'description': user.email,
			'url': f'/users/{user.id}'
		})
	
	return jsonify(results)

@api_bp.route('/activity', methods=['GET'])
@api_auth_required
def api_activity():
	"""Get recent activity feed."""
	from models import Project, Task, Comment
	from sqlalchemy import desc
	
	activities = []
	
	# Recent projects
	recent_projects = Project.query.order_by(desc(Project.created_at)).limit(3).all()
	for project in recent_projects:
		activities.append({
			'type': 'created',
			'text': f'New project "{project.title}" created',
			'time': project.created_at.strftime('%Y-%m-%d %H:%M'),
			'icon': 'plus'
		})
	
	# Recent task updates (fallback if created_at missing in some rows)
	try:
		recent_tasks = Task.query.order_by(desc(Task.created_at)).limit(3).all()
	except Exception:
		recent_tasks = Task.query.order_by(desc(Task.id)).limit(3).all()
	for task in recent_tasks:
		when = getattr(task, 'created_at', None) or datetime.utcnow()
		activities.append({
			'type': 'updated',
			'text': f'Task "{task.title}" updated',
			'time': when.strftime('%Y-%m-%d %H:%M'),
			'icon': 'edit'
		})
	
	# Sort by time
	activities.sort(key=lambda x: x['time'], reverse=True)
	
	return jsonify(activities[:10])

@api_bp.route('/projects/<int:project_id>/analytics', methods=['GET'])
@api_auth_required
def api_project_analytics(project_id):
	"""Get detailed analytics for a specific project."""
	from models import Project, Task
	
	project = Project.query.get_or_404(project_id)
	
	# Task breakdown by status
	status_breakdown = db.session.query(
		Task.status,
		func.count(Task.id).label('count')
	).filter_by(project_id=project_id).group_by(Task.status).all()
	
	# Priority breakdown
	priority_breakdown = db.session.query(
		Task.priority,
		func.count(Task.id).label('count')
	).filter_by(project_id=project_id).group_by(Task.priority).all()
	
	# Team productivity
	team_productivity = db.session.query(
		User.username,
		func.count(Task.id).label('task_count'),
		func.sum(func.case([(Task.status == 'Done', 1)], else_=0)).label('completed')
	).join(Task.assignees).filter(
		Task.project_id == project_id
	).group_by(User.id, User.username).all()
	
	return jsonify({
		'project': {
			'id': project.id,
			'title': project.title,
			'description': project.description,
			'progress': project.progress()
		},
		'status_breakdown': [{'status': row.status, 'count': row.count} for row in status_breakdown],
		'priority_breakdown': [{'priority': row.priority, 'count': row.count} for row in priority_breakdown],
		'team_productivity': [{
			'username': row.username,
			'task_count': row.task_count,
			'completed': row.completed or 0
		} for row in team_productivity]
	})

@api_bp.route('/reports/generate', methods=['POST'])
@api_auth_required
def api_generate_report():
	"""Generate comprehensive project reports."""
	from models import Project, Task, User
	import io
	import csv
	
	report_type = request.json.get('type', 'project')
	project_id = request.json.get('project_id')
	
	if report_type == 'project' and project_id:
		project = Project.query.get_or_404(project_id)
		tasks = Task.query.filter_by(project_id=project_id).all()
		
		# Create CSV report
		output = io.StringIO()
		writer = csv.writer(output)
		
		# Write header
		writer.writerow(['Task ID', 'Title', 'Description', 'Status', 'Priority', 'Due Date', 'Assignees'])
		
		# Write data
		for task in tasks:
			assignees = '; '.join([user.username for user in task.assignees])
			writer.writerow([
				task.id,
				task.title,
				task.description or '',
				task.status,
				task.priority,
				task.due_date.isoformat() if task.due_date else '',
				assignees
			])
		
		output.seek(0)
		return Response(
			output.getvalue(),
			mimetype='text/csv',
			headers={'Content-Disposition': f'attachment; filename=project_{project_id}_report.csv'}
		)
	
	return jsonify({'error': 'Invalid report type'}), 400

@api_bp.route('/notifications', methods=['GET'])
@api_auth_required
def api_notifications():
	"""Get user notifications."""
	# This would integrate with a notification system
	notifications = [
		{
			'id': 1,
			'title': 'Task Assigned',
			'message': 'You have been assigned to "API Development" task',
			'type': 'info',
			'created_at': '2024-01-15T10:30:00Z',
			'read': False
		},
		{
			'id': 2,
			'title': 'Project Deadline',
			'message': 'Project "Mobile App" deadline is approaching',
			'type': 'warning',
			'created_at': '2024-01-15T09:15:00Z',
			'read': False
		},
		{
			'id': 3,
			'title': 'Task Completed',
			'message': 'Task "Design Review" has been completed',
			'type': 'success',
			'created_at': '2024-01-15T08:45:00Z',
			'read': True
		}
	]
	
	return jsonify(notifications)