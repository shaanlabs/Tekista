from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from . import tasks_bp
from .forms import TaskForm, UpdateStatusForm, CommentForm
from models import Task, Project, User, Comment
from notifications import notify_task_assigned, notify_task_status_change
import json

def _availability_rank(av):
    order = {
        'Available': 3,
        'On a Break': 2,
        'In a Meeting': 1,
        'Busy': 0,
        'Out of Office': -1,
        None: 0
    }
    return order.get(av, 0)

def _auto_assign(task: Task, candidates):
    """Pick a single user using simple heuristic: prefer availability then lowest workload."""
    viable = [u for u in candidates if getattr(u, 'availability', 'Available') != 'Out of Office']
    if not viable:
        return None
    viable.sort(key=lambda u: (-_availability_rank(getattr(u, 'availability', 'Available')), getattr(u, 'current_workload', 100.0)))
    return viable[0]

def _workload_delta(task: Task):
    try:
        hours = float(task.estimated_hours or 4.0)
    except Exception:
        hours = 4.0
    # 40h work week
    return max(0.0, min(100.0, (hours / 40.0) * 100.0))

@tasks_bp.route('/')
@login_required
def list_tasks():
    status = request.args.get('status')
    assignee = request.args.get('assignee', type=int)
    project_id = request.args.get('project_id', type=int)

    q = Task.query
    if status:
        q = q.filter(Task.status == status)
    if assignee:
        q = q.join(Task.assignees).filter(User.id == assignee)
    if project_id:
        q = q.filter(Task.project_id == project_id)

    tasks = q.order_by(Task.due_date.is_(None), Task.due_date.asc()).all()
    users = User.query.order_by(User.username).all()
    projects = Project.query.order_by(Project.title).all()
    return render_template('tasks/list.html', tasks=tasks, users=users, projects=projects)

@tasks_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_task_global():
    # Only Admin/Manager can use global create
    role_name = getattr(getattr(current_user, 'role', None), 'name', None)
    if role_name not in ('Admin', 'Manager'):
        abort(403)
    projects = Project.query.order_by(Project.title).all()
    users = User.query.order_by(User.username).all()
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        due_date = request.form.get('due_date')
        priority = request.form.get('priority') or 'Normal'
        project_id = request.form.get('project_id', type=int)
        estimated_hours = request.form.get('estimated_hours', type=float)
        assignees_ids = request.form.getlist('assignees')
        if not title or not project_id:
            flash('Title and Project are required', 'warning')
            return render_template('tasks/create_global.html', projects=projects, users=users)
        project = db.session.get(Project, project_id) or abort(404)
        t = Task(title=title, description=description, priority=priority, project=project)
        if estimated_hours is not None:
            try:
                t.estimated_hours = float(estimated_hours)
            except Exception:
                pass
        # parse due_date
        try:
            if due_date:
                from datetime import date
                t.due_date = date.fromisoformat(due_date)
        except Exception:
            pass
        # assignees
        for uid in assignees_ids:
            u = db.session.get(User, int(uid))
            if u:
                t.assignees.append(u)
        # auto-assign if none provided
        if not t.assignees:
            # prefer project members as candidates, else all users
            candidates = project.users if project.users else User.query.all()
            pick = _auto_assign(t, candidates)
            if pick:
                t.assignees.append(pick)
                try:
                    pick.current_workload = min(100.0, (pick.current_workload or 0.0) + _workload_delta(t))
                except Exception:
                    pass
        db.session.add(t); db.session.commit()
        # process event: task created
        try:
            from models import ProcessEvent
            db.session.add(ProcessEvent(source='web', entity='task', entity_id=t.id, event_type='created', meta=f'project={project.id if project else project_id}'))
            db.session.commit()
        except Exception:
            pass
        # notify
        try:
            notify_task_assigned(t)
        except Exception:
            pass
        flash('Task added', 'success')
        return redirect(url_for('tasks.task_detail', task_id=t.id))
    return render_template('tasks/create_global.html', projects=projects, users=users)

@tasks_bp.route('/create/<int:project_id>', methods=['GET', 'POST'])
@login_required
def create_task(project_id):
    project = Project.query.get_or_404(project_id)
    # Only Admin/Manager or project members can create within a project
    role_name = getattr(getattr(current_user, 'role', None), 'name', None)
    if role_name not in ('Admin', 'Manager') and current_user not in project.users:
        abort(403)
    form = TaskForm()
    form.assignees.choices = [(u.id, u.username) for u in User.query.order_by(User.username).all()]
    form.dependencies.choices = [(t.id, t.title) for t in project.tasks]
    if form.validate_on_submit():
        t = Task(title=form.title.data, description=form.description.data, due_date=form.due_date.data, priority=form.priority.data, project=project)
        if getattr(form, 'estimated_hours', None) and form.estimated_hours.data is not None:
            try:
                t.estimated_hours = float(form.estimated_hours.data)
            except Exception:
                pass
        for uid in form.assignees.data:
            u = db.session.get(User, uid)
            if u:
                t.assignees.append(u)
        # auto-assign if none provided
        if not t.assignees:
            candidates = project.users if project.users else User.query.all()
            pick = _auto_assign(t, candidates)
            if pick:
                t.assignees.append(pick)
                try:
                    pick.current_workload = min(100.0, (pick.current_workload or 0.0) + _workload_delta(t))
                except Exception:
                    pass
        for dep_id in form.dependencies.data:
            pre = db.session.get(Task, dep_id)
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

@tasks_bp.route('/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = db.session.get(Task, task_id) or abort(404)
    form = TaskForm(obj=task)
    # populate choices
    form.assignees.choices = [(u.id, u.username) for u in User.query.order_by(User.username).all()]
    if task.project:
        form.dependencies.choices = [(t.id, t.title) for t in task.project.tasks if t.id != task.id]
    else:
        form.dependencies.choices = []
    if form.validate_on_submit():
        task.title = form.title.data
        task.description = form.description.data
        task.due_date = form.due_date.data
        task.priority = form.priority.data
        # update assignees
        task.assignees.clear()
        for uid in form.assignees.data:
            u = db.session.get(User, uid)
            if u:
                task.assignees.append(u)
        # update predecessors
        task.predecessors.clear()
        for dep_id in form.dependencies.data:
            pre = db.session.get(Task, dep_id)
            if pre:
                task.predecessors.append(pre)
        db.session.commit()
        flash('Task updated', 'success')
        return redirect(url_for('tasks.task_detail', task_id=task.id))
    return render_template('tasks/edit.html', form=form, task=task)


@tasks_bp.route('/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    project_id = task.project_id
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted', 'success')
    if project_id:
        return redirect(url_for('projects.project_detail', project_id=project_id))
    return redirect(url_for('tasks.list_tasks'))


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
        # Permission: only assignees or Admin/Manager can update to Completed
        role_name = getattr(getattr(current_user, 'role', None), 'name', None)
        is_assignee = current_user in task.assignees
        if new_status == 'Completed' and not (is_assignee or role_name in ('Admin','Manager')):
            flash('Only assignees or managers can mark a task Completed', 'warning')
            return redirect(url_for('tasks.task_detail', task_id=task.id))
        if new_status in ('In Progress', 'To Do', 'Completed') or (new_status == 'In Progress' and task.can_start()):
            task.status = new_status
            db.session.commit()
            # process event: status change
            try:
                from models import ProcessEvent
                db.session.add(ProcessEvent(source='web', entity='task', entity_id=task.id, event_type='status_changed', meta=f'{old_status}->{new_status}'))
                db.session.commit()
            except Exception:
                pass
            # anomaly: premature completion for parent with incomplete subtasks
            try:
                if new_status == 'Completed' and task.subtasks:
                    total = len(task.subtasks)
                    done = sum(1 for st in task.subtasks if st.status == 'Completed')
                    ratio = (done / max(1, total))
                    if ratio < 1.0:
                        from models import AnomalyEvent
                        evidence = {
                            'parent_task_id': task.id,
                            'subtasks_total': total,
                            'subtasks_completed': done,
                            'completion_ratio': ratio,
                        }
                        db.session.add(AnomalyEvent(
                            user_id=getattr(current_user,'id', None),
                            severity='medium',
                            type='premature_completion',
                            evidence_json=json.dumps(evidence),
                            explanation_json=json.dumps({'reason':'Parent Completed while subtasks incomplete'})
                        ))
                        db.session.commit()
            except Exception:
                pass
            # workload adjustment when moved to Completed from a non-completed state
            try:
                if new_status == 'Completed' and old_status != 'Completed':
                    delta = _workload_delta(task)
                    for u in task.assignees:
                        u.current_workload = max(0.0, (u.current_workload or 0.0) - delta)
                    db.session.commit()
            except Exception:
                pass
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
        db.session.add(c)
        db.session.commit()
        flash('Comment added', 'success')
        return redirect(url_for('tasks.task_detail', task_id=task.id))
    return render_template('tasks/detail.html', task=task, form=status_form, comment_form=comment_form)

