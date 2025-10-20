from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from . import tasks_bp
from .forms import TaskForm, UpdateStatusForm, CommentForm
from models import Task, Project, User, Comment
from notifications import notify_task_assigned, notify_task_status_change

@tasks_bp.route('/create/<int:project_id>', methods=['GET', 'POST'])
@login_required
def create_task(project_id):
	project = Project.query.get_or_404(project_id)
	form = TaskForm()
	form.assignees.choices = [(u.id, u.username) for u in User.query.order_by(User.username).all()]
	form.dependencies.choices = [(t.id, t.title) for t in project.tasks]
	if form.validate_on_submit():
		t = Task(title=form.title.data, description=form.description.data, due_date=form.due_date.data, priority=form.priority.data, project=project)
		for uid in form.assignees.data:
			u = User.query.get(uid)
			if u:
				t.assignees.append(u)
		for dep_id in form.dependencies.data:
			pre = Task.query.get(dep_id)
			if pre:
				t.predecessors.append(pre)
		db.session.add(t); db.session.commit()
		# Notify assignees (if emails configured)
		try:
			notify_task_assigned(t)
		except Exception:
			pass
		flash('Task added', 'success')
		return redirect(url_for('projects.project_detail', project_id=project.id))
	return render_template('tasks/create.html', form=form, project=project)

@tasks_bp.route('/<int:task_id>', methods=['GET', 'POST'])
@login_required
def task_detail(task_id):
	task = Task.query.get_or_404(task_id)
	status_form = UpdateStatusForm(status=task.status)
	comment_form = CommentForm()
	# handle status update
	if status_form.validate_on_submit() and status_form.submit.data:
		old_status = task.status
		new_status = status_form.status.data
		if new_status in ('In Progress','To Do') or (new_status == 'In Progress' and task.can_start()):
			task.status = new_status
			db.session.commit()
			# Notify about status change
			try:
				notify_task_status_change(task, old_status, new_status)
			except Exception:
				pass
			flash('Status updated', 'success')
		else:
			if not task.can_start():
				flash('Cannot start task until predecessors are Done', 'warning')
		return redirect(url_for('tasks.task_detail', task_id=task.id))
	# handle comment POST
	if comment_form.validate_on_submit() and comment_form.submit.data:
		c = Comment(body=comment_form.body.data, author_id=current_user.id, task_id=task.id)
		db.session.add(c); db.session.commit()
		flash('Comment added', 'success')
		return redirect(url_for('tasks.task_detail', task_id=task.id))
	return render_template('tasks/detail.html', task=task, form=status_form, comment_form=comment_form)
