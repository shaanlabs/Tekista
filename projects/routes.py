# from flask import render_template, redirect, url_for, flash, request, Response
# from flask_login import login_required, current_user
# from app import db
# from . import projects_bp
# from .forms import ProjectForm
# from models import Project, User, Task
# from datetime import datetime

# @projects_bp.route('/')
# @login_required
# def list_projects():
# 	query = Project.query
# 	# simple filters: status, assignee, deadline
# 	status = request.args.get('status')
# 	assignee = request.args.get('assignee', type=int)
# 	deadline = request.args.get('deadline')
# 	if status:
# 		query = query.join(Task).filter(Task.status==status).distinct()
# 	if assignee:
# 		query = query.join(Project.users).filter(User.id==assignee)
# 	if deadline:
# 		try:
# 			d = datetime.strptime(deadline, '%Y-%m-%d').date()
# 			query = query.filter(Project.deadline <= d)
# 		except:
# 			pass
# 	projects = query.all()
# 	users = User.query.all()
# 	return render_template('projects/list.html', projects=projects, users=users)

# @projects_bp.route('/create', methods=['GET', 'POST'])
# @login_required
# def create_project():
# 	form = ProjectForm()
# 	form.users.choices = [(u.id, u.username) for u in User.query.order_by(User.username).all()]
# 	if form.validate_on_submit():
# 		p = Project(title=form.title.data, description=form.description.data, deadline=form.deadline.data)
# 		# assign users
# 		for uid in form.users.data:
# 			u = User.query.get(uid)
# 			if u:
# 				p.users.append(u)
# 		db.session.add(p); db.session.commit()
# 		flash('Project created', 'success')
# 		return redirect(url_for('projects.list_projects'))
# 	return render_template('projects/create.html', form=form)

# @projects_bp.route('/<int:project_id>')
# @login_required
# def project_detail(project_id):
# 	p = Project.query.get_or_404(project_id)
# 	# optional filtering of tasks
# 	status = request.args.get('status')
# 	assignee = request.args.get('assignee', type=int)
# 	tasks = p.tasks
# 	if status:
# 		tasks = [t for t in tasks if t.status == status]
# 	if assignee:
# 		tasks = [t for t in tasks if any(u.id == assignee for u in t.assignees)]
# 	return render_template('projects/detail.html', project=p, tasks=tasks)

# @projects_bp.route('/<int:project_id>/export')
# @login_required
# def export_project_csv(project_id):
# 	p = Project.query.get_or_404(project_id)
# 	import io, csv
# 	s = io.StringIO()
# 	w = csv.writer(s)
# 	# header
# 	w.writerow(['Task ID','Title','Description','Status','Priority','Due Date','Assignees'])
# 	for t in p.tasks:
# 		assignees = ";".join([u.username for u in t.assignees])
# 		w.writerow([t.id, t.title, (t.description or "").replace("\n"," "), t.status, t.priority, t.due_date, assignees])
# 	output = s.getvalue()
# 	s.close()
# 	filename = f'project_{p.id}_tasks.csv'
# 	return Response(output, mimetype='text/csv', headers={"Content-Disposition": f"attachment;filename={filename}"})
# projects/routes.py
from flask import render_template, redirect, url_for, flash, request, Response, abort
from flask_login import login_required, current_user
from sqlalchemy import exists
from sqlalchemy.orm import selectinload

# Relative imports to avoid circular dependencies
from models import Project, User, Task, db
from . import projects_bp
from .forms import ProjectForm
from datetime import datetime


@projects_bp.route('/')
@login_required
def list_projects():
    # Start with base query and eager-load relationships to avoid N+1
    query = Project.query.options(
        selectinload(Project.users),
        selectinload(Project.tasks)
    )

    # Get filter parameters
    status = request.args.get('status')
    assignee = request.args.get('assignee', type=int)
    deadline = request.args.get('deadline')

    # Filter by task status (projects that have at least one task with this status)
    if status:
        query = query.filter(
            exists().where(Task.project_id == Project.id).where(Task.status == status)
        )

    # Filter by assigned user
    if assignee:
        query = query.filter(Project.users.any(User.id == assignee))

    # Filter by deadline
    if deadline:
        try:
            d = datetime.strptime(deadline, '%Y-%m-%d').date()
            query = query.filter(Project.deadline <= d)
        except ValueError:
            flash('Invalid date format. Use YYYY-MM-DD.', 'warning')

    projects = query.all()
    users = User.query.order_by(User.username).all()
    return render_template('projects/list.html', projects=projects, users=users)


@projects_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_project():
    form = ProjectForm()
    # Dynamically set user choices for the multi-select field
    form.users.choices = [(u.id, u.username) for u in User.query.order_by(User.username)]

    if form.validate_on_submit():
        project = Project(
            title=form.title.data,
            description=form.description.data,
            deadline=form.deadline.data
        )
        # Associate selected users
        for user_id in form.users.data:
            user = User.query.get(user_id)
            if user:
                project.users.append(user)

        db.session.add(project)
        db.session.commit()
        flash('Project created successfully!', 'success')
        return redirect(url_for('projects.list_projects'))

    return render_template('projects/create.html', form=form)


@projects_bp.route('/create-smart', methods=['GET', 'POST'])
@login_required
def create_project_smart():
    # Only Admin/Manager can access smart create
    role_name = getattr(getattr(current_user, 'role', None), 'name', None)
    if role_name not in ('Admin','Manager','Project Manager'):
        abort(403)
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        title = data.get('title')
        if not title:
            return {'error':'title required'}, 400
        p = Project(title=title, description=data.get('description'))
        # deadline
        dl = data.get('deadline')
        if dl:
            try:
                p.deadline = datetime.fromisoformat(dl).date()
            except Exception:
                pass
        # Attach PM and team members
        pm_id = data.get('project_manager_id')
        team_ids = data.get('team_member_ids', []) or []
        try:
            if pm_id:
                pm = User.query.get(int(pm_id))
                if pm:
                    p.users.append(pm)
            for uid in team_ids:
                u = User.query.get(int(uid))
                if u and u not in p.users:
                    p.users.append(u)
        except Exception:
            pass
        db.session.add(p); db.session.commit()
        return {'id': p.id}, 201
    # GET renders smart UI
    return render_template('projects/create_smart.html')


@projects_bp.route('/<int:project_id>')
@login_required
def project_detail(project_id):
    # Eager-load tasks and their assignees to avoid N+1 in template
    project = Project.query.options(
        selectinload(Project.tasks).selectinload(Task.assignees)
    ).get_or_404(project_id)

    # Build task query based on filters
    task_query = Task.query.filter_by(project_id=project_id)

    status = request.args.get('status')
    assignee = request.args.get('assignee', type=int)

    if status:
        task_query = task_query.filter(Task.status == status)
    if assignee:
        # Join the User relationship and filter by User.id
        task_query = task_query.join(Task.assignees).join(User).filter(User.id == assignee)

    tasks = task_query.all()
    return render_template('projects/detail.html', project=project, tasks=tasks)


@projects_bp.route('/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    form = ProjectForm(obj=project)
    form.users.choices = [(u.id, u.username) for u in User.query.order_by(User.username)]
    if form.validate_on_submit():
        project.title = form.title.data
        project.description = form.description.data
        project.deadline = form.deadline.data
        # update users
        project.users.clear()
        for user_id in form.users.data:
            user = User.query.get(user_id)
            if user:
                project.users.append(user)
        db.session.commit()
        flash('Project updated successfully!', 'success')
        return redirect(url_for('projects.project_detail', project_id=project.id))
    return render_template('projects/edit.html', form=form, project=project)


@projects_bp.route('/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    flash('Project deleted', 'success')
    return redirect(url_for('projects.list_projects'))


# Kanban Board View
@projects_bp.route('/<int:project_id>/kanban')
@login_required
def project_kanban(project_id):
    project = Project.query.get_or_404(project_id)
    # Group tasks by status
    columns = {
        'To Do': [],
        'In Progress': [],
        'Done': []
    }
    for t in project.tasks:
        columns.setdefault(t.status, []).append(t)
    return render_template('projects/kanban.html', project=project, columns=columns)


# Gantt Chart View (basic scaffold - client renders timeline)
@projects_bp.route('/<int:project_id>/gantt')
@login_required
def project_gantt(project_id):
    project = Project.query.get_or_404(project_id)
    tasks = Task.query.filter_by(project_id=project_id).all()
    return render_template('projects/gantt.html', project=project, tasks=tasks)


@projects_bp.route('/<int:project_id>/export')
@login_required
def export_project_csv(project_id):
    # Admin only
    if not (getattr(current_user, 'role', None) and getattr(current_user.role, 'name', None) == 'Admin'):
        abort(403)
    project = Project.query.get_or_404(project_id)

    from io import StringIO
    import csv

    si = StringIO()
    writer = csv.writer(si)

    # Write header
    writer.writerow([
        'Task ID', 'Title', 'Description', 'Status',
        'Priority', 'Due Date', 'Assignees'
    ])

    # Write rows
    for task in project.tasks:
        assignee_usernames = ";".join(u.username for u in task.assignees)
        due_date_str = task.due_date.isoformat() if task.due_date else ""
        writer.writerow([
            task.id,
            task.title,
            task.description or "",
            task.status,
            task.priority,
            due_date_str,
            assignee_usernames
        ])

    output = si.getvalue()
    si.close()

    # Audit log
    try:
        db.session.add(AuditLog(
            actor_id=current_user.id,
            action='export_csv',
            target_type='project',
            target_id=project.id,
            meta=f'CSV export: project_{project.id}_tasks.csv'
        ))
        db.session.commit()
    except Exception:
        pass

    filename = f'project_{project.id}_tasks.csv'
    return Response(
        output,
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )