from flask import jsonify, request, url_for, g
from flask_login import login_required
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
