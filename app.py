#     # RBAC helper
# def require_roles(*roles):
#         def decorator(fn):
#             def wrapper(*args, **kwargs):
#                 if not current_user.is_authenticated:
#                     return login_manager.unauthorized()
#                 user_role = getattr(current_user, 'role', None)
#                 name = getattr(user_role, 'name', None)
#                 if roles and name not in roles:
#                     return jsonify({"error":"forbidden"}), 403
#                 return fn(*args, **kwargs)
#             wrapper.__name__ = fn.__name__
#             return wrapper
#         return decorator

# app.py
from flask import Flask, render_template, session, jsonify, request, send_from_directory, redirect, url_for, abort
from flask_login import LoginManager, login_required, current_user
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect, generate_csrf
import os
import sys
import logging
from functools import wraps
from werkzeug.utils import secure_filename
import json
from datetime import datetime, date, timedelta
import time
 

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, User
from config import Config
from socket_events import init_socketio

# Initialize extensions (using the SAME db from models.py)
login_manager = LoginManager()
login_manager.login_view = "auth.login"
mail = Mail()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(Config)

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    # Configure user loader
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except Exception:
            return None

    # Initialize CSRF protection
    csrf = CSRFProtect()
    csrf.init_app(app)

    # expose csrf_token() to templates (so {{ csrf_token() }} works)
    @app.context_processor
    def inject_csrf_token():
        return {"csrf_token": generate_csrf}

    # Register blueprints
    from auth import auth_bp
    from projects.routes import projects_bp
    from tasks.routes import tasks_bp
    from api.routes import api_bp
    from ai.routes import aibp as ai_bp
    from notifications_routes import notifications_bp

    # register blueprint at root so routes like /login are available
    # (previously registered with url_prefix='/auth' which caused 404s for /login)
    app.register_blueprint(auth_bp)  # removed url_prefix='/auth'

    app.register_blueprint(projects_bp, url_prefix="/projects")
    app.register_blueprint(tasks_bp, url_prefix="/tasks")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(ai_bp, url_prefix="/ai")
    app.register_blueprint(notifications_bp)

    # CSRF exemptions for JSON APIs used by frontend fetch
    try:
        csrf.exempt(api_bp)
        csrf.exempt(ai_bp)
        csrf.exempt(notifications_bp)
    except Exception:
        pass
    # Enterprise removed

    # Initialize Socket.IO and attach to app extensions for global access
    socketio = init_socketio(app)
    app.extensions['socketio'] = socketio

    # Error handler for AI features
    @app.errorhandler(500)
    def handle_server_error(e):
        app.logger.error(f'Server Error: {str(e)}')
        if request.path.startswith('/api/') or request.path.startswith('/ai/'):
            return jsonify({"error": "An internal server error occurred"}), 500
        return render_template('500.html'), 500

    @app.errorhandler(404)
    def handle_not_found(e):
        if request.path.startswith('/api/') or request.path.startswith('/ai/'):
            return jsonify({"error": "Resource not found"}), 404
        return render_template('404.html'), 404

    # RBAC helper
    def require_roles(*roles):
        def decorator(fn):
            def wrapper(*args, **kwargs):
                if not current_user.is_authenticated:
                    return login_manager.unauthorized()
                user_role = getattr(current_user, 'role', None)
                name = getattr(user_role, 'name', None)
                if roles and name not in roles:
                    return jsonify({"error":"forbidden"}), 403
                return fn(*args, **kwargs)
            wrapper.__name__ = fn.__name__
            return wrapper
        return decorator

    # Add index route -> use new dashboard as the home page
    @app.route('/')
    @login_required
    def index():
        return render_template('dashboard.html')
    
    # Ancillary pages (placeholder scaffolds)
    @app.route('/inbox')
    @login_required
    def inbox():
        return render_template('pages/inbox.html')

    @app.route('/calendar')
    @login_required
    def calendar():
        return render_template('pages/calendar.html')

    @app.route('/teams')
    @login_required
    def teams():
        from models import User
        users = User.query.order_by(User.username).all()
        return render_template('pages/teams.html', users=users)

    @app.route('/files')
    @login_required
    def files():
        from models import Project
        import os
        pid = request.args.get('project_id', type=int)
        projects = Project.query.order_by(Project.title).all()
        current_project = None
        files = []
        if pid:
            current_project = Project.query.get(pid)
            upload_root = os.path.join(app.root_path, 'uploads')
            project_dir = os.path.join(upload_root, str(pid))
            os.makedirs(project_dir, exist_ok=True)
            try:
                files = os.listdir(project_dir)
            except Exception:
                files = []
        return render_template('pages/files.html', projects=projects, current_project=current_project, files=files)

    @app.route('/reports')
    @login_required
    @require_roles('Admin')
    def reports():
        from models import Project
        projects = Project.query.order_by(Project.created_at.desc()).all()
        return render_template('pages/reports.html', projects=projects)

    @app.route('/settings')
    @login_required
    def settings():
        return render_template('pages/settings.html')

    @app.route('/help')
    @login_required
    def help():
        return render_template('pages/help.html')

    # AI Assistant simple UI
    @app.route('/ai-assistant')
    @login_required
    def ai_assistant():
        return render_template('pages/ai.html')

    # Simple pages for advanced modules (placeholders)
    @app.route('/workflows')
    @login_required
    def workflows():
        return render_template('pages/workflows.html')

    @app.route('/automations')
    @login_required
    def automations():
        return render_template('pages/automations.html')

    @app.route('/analytics/overview')
    @login_required
    def analytics_overview():
        return render_template('pages/analytics_overview.html')

    @app.route('/squads')
    @login_required
    def squads():
        return render_template('pages/squads.html')

    # Minimal AI endpoints for frontend fetch
    @app.route('/ai/chat', methods=['POST'])
    @login_required
    @csrf.exempt
    def ai_chat_post():
        try:
            data = request.get_json(silent=True) or {}
            prompt = data.get('message') or data.get('prompt') or data.get('text') or ''
            if not prompt:
                # accept form-encoded fallback
                prompt = request.form.get('message') or request.form.get('prompt') or ''
            # always return 200 with a reply to avoid UX error bubbles
            reply = f"Received: {prompt}" if prompt else "Hello! Ask me about projects, tasks, or summaries."
            return jsonify({"reply": reply})
        except Exception as e:
            return jsonify({"reply":"Temporary AI error. Please try again."}), 200

    @app.route('/ai/summary', methods=['POST'])
    @login_required
    @csrf.exempt
    def ai_summary_post():
        data = request.get_json(silent=True) or {}
        text = data.get('text') or ''
        return jsonify({"summary": f"Summary: {text[:200]}"})

    @app.route('/ai/risks', methods=['POST'])
    @login_required
    @csrf.exempt
    def ai_risks_post():
        data = request.get_json(silent=True) or {}
        text = data.get('text') or ''
        return jsonify({"reply": f"Potential risks identified for: {text[:200]}"})

    # AI Project Manager (Agentic) endpoints
    @app.route('/ai/pm/decompose', methods=['POST'])
    @login_required
    @csrf.exempt
    def ai_pm_decompose():
        from models import AIAgentJob, db as _db
        payload = request.get_json(silent=True) or {}
        goal = payload.get('goal') or ''
        # stub plan
        plan = {
            'goal': goal,
            'tasks': [
                {'title':'Draft brief','order':1},
                {'title':'Design assets','order':2},
                {'title':'Implement','order':3},
                {'title':'QA & Publish','order':4},
            ]
        }
        try:
            job = AIAgentJob(job_type='decompose', payload_json=json.dumps(payload), created_by=current_user.id)
            _db.session.add(job); _db.session.commit()
        except Exception:
            pass
        return jsonify({'plan': plan})

    @app.route('/ai/pm/apply-plan', methods=['POST'])
    @login_required
    @csrf.exempt
    def ai_pm_apply_plan():
        from models import AIAgentJob, AIAuditLog, Project, Task, db as _db
        role_name = getattr(getattr(current_user, 'role', None), 'name', None)
        if role_name not in ('Admin','Manager'):
            return jsonify({'error':'manager approval required'}), 403
        data = request.get_json(silent=True) or {}
        project_id = data.get('project_id')
        plan = data.get('plan') or {}
        project = Project.query.get_or_404(project_id)
        # create basic tasks sequentially (no dependencies wiring here for brevity)
        created_ids = []
        for item in plan.get('tasks', []):
            t = Task(title=item.get('title','Untitled'), description=item.get('desc',''), priority=item.get('priority','Normal'), project=project)
            _db.session.add(t)
            created_ids.append(t)
        _db.session.commit()
        try:
            _db.session.add(AIAgentJob(job_type='apply_plan', payload_json=json.dumps(plan), created_by=current_user.id))
            _db.session.add(AIAuditLog(actor='AI-Agent-01', action='apply_plan', target_type='project', target_id=project.id, meta=f"created_tasks={len(created_ids)}"))
            _db.session.commit()
        except Exception:
            pass
        return jsonify({'ok': True, 'created_tasks': len(created_ids)})

    # Recommendations for assignees (session auth)
    @app.route('/api/recommendations', methods=['GET'])
    @login_required
    @csrf.exempt
    def api_recommendations():
        from models import Project, User
        try:
            project_id = request.args.get('project_id', type=int)
            limit = request.args.get('limit', default=3, type=int)
            priority = request.args.get('priority') or 'Normal'
            est = request.args.get('estimated_hours', type=float) or 4.0
            project = Project.query.get(project_id) if project_id else None
            # candidate pool
            candidates = project.users if project and project.users else User.query.all()
            # simple score: availability rank + inverse workload, tweak by priority
            def av_rank(av):
                order = {'Available':3,'On a Break':2,'In a Meeting':1,'Busy':0,'Out of Office':-1}
                return order.get(av, 0)
            alpha = {'Low':1.0,'Normal':1.0,'Medium':1.0,'High':0.9,'Critical':0.8}.get(priority,1.0)
            scored = []
            for u in candidates:
                if getattr(u,'availability','Available') == 'Out of Office':
                    continue
                wl = max(0.0, min(100.0, float(getattr(u,'current_workload',0.0))))
                wl_score = (1.0 - wl/100.0) ** alpha
                score = av_rank(getattr(u,'availability','Available')) + wl_score
                scored.append((score,u,wl))
            scored.sort(key=lambda x: x[0], reverse=True)
            out = []
            for score,u,wl in scored[:max(1,limit)]:
                out.append({
                    'user_id': u.id,
                    'username': u.username,
                    'availability': getattr(u,'availability','Available'),
                    'current_workload': wl,
                    'reason': f"availability={getattr(u,'availability','?')}, workload={wl}%"
                })
            return jsonify(out)
        except Exception as e:
            return jsonify([])

    # Availability setter (self or Admin/Manager)
    @app.route('/api/users/<int:user_id>/availability', methods=['POST'])
    @login_required
    @csrf.exempt
    def api_set_availability(user_id):
        from models import User
        target = User.query.get_or_404(user_id)
        role_name = getattr(getattr(current_user, 'role', None), 'name', None)
        if current_user.id != target.id and role_name not in ('Admin','Manager'):
            return jsonify({"error":"forbidden"}), 403
        data = request.get_json(silent=True) or {}
        status = data.get('status') or request.form.get('status')
        if not status:
            return jsonify({"error":"status required"}), 400
        target.availability = status
        try:
            from models import AuditLog
            db.session.add(AuditLog(actor_id=current_user.id, action='set_availability', target_type='user', target_id=target.id, meta=status))
        except Exception:
            pass
        db.session.commit()
        return jsonify({"ok": True, "user_id": target.id, "availability": target.availability})
    # Upload endpoint for files
    @app.route('/files/upload', methods=['POST'])
    @login_required
    @require_roles('Admin')
    def files_upload():
        import os
        pid = request.form.get('project_id', type=int)
        f = request.files.get('file')
        if not pid or not f:
            return render_template('pages/files.html'), 400
        filename = secure_filename(f.filename)
        upload_root = os.path.join(app.root_path, 'uploads')
        project_dir = os.path.join(upload_root, str(pid))
        os.makedirs(project_dir, exist_ok=True)
        f.save(os.path.join(project_dir, filename))
        # Audit log
        try:
            from models import AuditLog
            db.session.add(AuditLog(
                actor_id=current_user.id,
                action='upload_file',
                target_type='project',
                target_id=pid,
                meta=filename
            ))
            db.session.commit()
        except Exception:
            pass
        return redirect(url_for('files', project_id=pid))

    # Background jobs: lightweight scheduler thread
    import threading, time
    def _calendar_capacity_sync_loop(app_ref):
        from models import User, UserCapacity, db as _db
        with app_ref.app_context():
            while True:
                try:
                    # stub: write today default capacity for all users if missing
                    from datetime import date
                    today = date.today()
                    users = User.query.all()
                    for u in users:
                        exists = UserCapacity.query.filter_by(user_id=u.id, date=today).first()
                        if not exists:
                            uc = UserCapacity(user_id=u.id, date=today, blocked_hours=0.0, capacity_hours=8.0, source='manual')
                            _db.session.add(uc)
                    _db.session.commit()
                except Exception:
                    _db.session.rollback()
                time.sleep(900)  # 15 minutes

    def _ml_skill_updater_loop(app_ref):
        from models import TaskOutcome, UserSkillHistory, db as _db
        with app_ref.app_context():
            while True:
                try:
                    # stub: no-op placeholder
                    pass
                except Exception:
                    _db.session.rollback()
                time.sleep(1800)  # 30 minutes

    def _reliability_recompute_loop(app_ref):
        from models import AnomalyEvent, User, UserReliabilityScore, db as _db
        from sqlalchemy import func
        with app_ref.app_context():
            while True:
                try:
                    users = User.query.all()
                    now = datetime.utcnow()
                    since = now - timedelta(days=30)
                    type_weights = {
                        'integrity_mismatch': 10.0,
                        'premature_completion': 5.0,
                        'after_hours_spike': 4.0,
                        'extreme_deviation': 8.0,
                    }
                    for u in users:
                        q = AnomalyEvent.query.filter(AnomalyEvent.user_id==u.id, AnomalyEvent.occurred_at >= since)
                        items = q.order_by(AnomalyEvent.occurred_at.desc()).limit(1000).all()
                        score = 100.0
                        last_penalized_at = {}
                        for a in items:
                            days = max(0, (now - a.occurred_at).days)
                            decay = 0.92 ** days
                            w = type_weights.get(a.type, 5.0)
                            # cooldown: penalize at most once per 24h per type
                            if a.type in last_penalized_at and (last_penalized_at[a.type] - a.occurred_at).total_seconds() < 86400:
                                continue
                            last_penalized_at[a.type] = a.occurred_at
                            score -= w * decay
                        score = max(0.0, min(100.0, score))
                        row = UserReliabilityScore.query.filter_by(user_id=u.id).order_by(UserReliabilityScore.computed_at.desc()).first()
                        if not row or abs(row.score - score) > 0.1:
                            _db.session.add(UserReliabilityScore(user_id=u.id, score=score, computed_at=now))
                    _db.session.commit()
                except Exception:
                    _db.session.rollback()
                time.sleep(3600)  # hourly

    def _integrity_mismatch_detector_loop(app_ref):
        from models import UserDailyFeature, AnomalyEvent, db as _db
        with app_ref.app_context():
            while True:
                try:
                    today = date.today()
                    # Expected feature keys
                    # time_logged_coding_hours, commits_count, activity_active_hours, meeting_hours
                    rows = UserDailyFeature.query.filter_by(date=today).all()
                    by_user = {}
                    for r in rows:
                        by_user.setdefault(r.user_id, {})[r.feature_key] = r.value
                    for uid, feats in by_user.items():
                        tl = float(feats.get('time_logged_coding_hours', 0.0))
                        commits = float(feats.get('commits_count', 0.0))
                        active = float(feats.get('activity_active_hours', 0.0))
                        meets = float(feats.get('meeting_hours', 0.0))
                        if tl >= 6.0 and commits == 0.0 and active < 2.0:
                            evidence = {
                                'time_logged_coding_hours': tl,
                                'commits_count': commits,
                                'activity_active_hours': active,
                                'meeting_hours': meets,
                                'date': today.isoformat()
                            }
                            base_center = None; base_spread = None; z = None
                            try:
                                from models import UserBehaviorBaseline
                                base = UserBehaviorBaseline.query.filter_by(user_id=uid, metric_key='time_logged_coding_hours').first()
                                if base and base.spread:
                                    base_center, base_spread = base.center, base.spread
                                    z = (tl - (base_center or 0.0)) / (base_spread or 1.0)
                            except Exception:
                                pass
                            _db.session.add(AnomalyEvent(user_id=uid, severity='high', type='integrity_mismatch', evidence_json=json.dumps(evidence), explanation_json=json.dumps({'reason':'Coding hours with no commits and low activity','baseline':{'center':base_center,'spread':base_spread},'z_score':z})))
                    _db.session.commit()
                except Exception:
                    _db.session.rollback()
                time.sleep(600)  # 10 minutes

    def _after_hours_detector_loop(app_ref):
        from models import UserDailyFeature, AnomalyEvent, db as _db
        with app_ref.app_context():
            while True:
                try:
                    today = date.today()
                    rows = UserDailyFeature.query.filter_by(date=today).all()
                    by_user = {}
                    for r in rows:
                        by_user.setdefault(r.user_id, {})[r.feature_key] = r.value
                    for uid, feats in by_user.items():
                        tl_total = float(feats.get('time_logged_total_hours', 0.0))
                        active = float(feats.get('activity_active_hours', 0.0))
                        # Simple heuristic: large logged hours with very low active time suggests after-hours logging spike
                        if tl_total >= 8.0 and active < 1.0:
                            evidence = {
                                'time_logged_total_hours': tl_total,
                                'activity_active_hours': active,
                                'date': today.isoformat()
                            }
                            _db.session.add(AnomalyEvent(user_id=uid, severity='medium', type='after_hours_spike', evidence_json=json.dumps(evidence), explanation_json=json.dumps({'reason':'Heavy logging with minimal active time, potential after-hours bulk updates'})))
                    _db.session.commit()
                except Exception:
                    _db.session.rollback()
                time.sleep(900)  # 15 minutes

    def _extreme_deviation_detector_loop(app_ref):
        from models import UserDailyFeature, UserBehaviorBaseline, AnomalyEvent, db as _db
        with app_ref.app_context():
            while True:
                try:
                    today = date.today()
                    # metric: tasks_completed_total (daily)
                    feat_key = 'tasks_completed_total'
                    feats = UserDailyFeature.query.filter_by(date=today, feature_key=feat_key).all()
                    for f in feats:
                        base = UserBehaviorBaseline.query.filter_by(user_id=f.user_id, metric_key=feat_key).first()
                        if not base or base.spread is None or base.spread <= 0:
                            continue
                        z = (f.value - (base.center or 0.0)) / (base.spread or 1.0)
                        if z > 4.0:
                            evidence = {
                                'value': f.value,
                                'baseline_center': base.center,
                                'baseline_spread': base.spread,
                                'z_score': z,
                                'date': today.isoformat()
                            }
                            _db.session.add(AnomalyEvent(user_id=f.user_id, severity='high', type='extreme_deviation', evidence_json=json.dumps(evidence), explanation_json=json.dumps({'reason':'Daily tasks completed far exceeds personal baseline','baseline':{'center':base.center,'spread':base.spread},'z_score':z})))
                    _db.session.commit()
                except Exception:
                    _db.session.rollback()
                time.sleep(900)  # 15 minutes

    def _hourly_rollup_loop(app_ref):
        from models import User, UserDailyFeature, UserCapacity, ProcessEvent, Task, db as _db
        from sqlalchemy import and_
        with app_ref.app_context():
            while True:
                try:
                    today = date.today()
                    users = User.query.all()
                    # Ensure baseline feature keys exist for today
                    base_keys = ['commits_count','meeting_hours','activity_active_hours','time_logged_coding_hours','time_logged_total_hours','tasks_completed_total']
                    for u in users:
                        existing = {r.feature_key: r for r in UserDailyFeature.query.filter_by(user_id=u.id, date=today).all()}
                        for k in base_keys:
                            if k not in existing:
                                _db.session.add(UserDailyFeature(user_id=u.id, date=today, feature_key=k, value=0.0, source='rollup'))
                    _db.session.commit()

                    # Update meeting_hours from UserCapacity (blocked_hours)
                    caps = UserCapacity.query.filter_by(date=today).all()
                    for c in caps:
                        r = UserDailyFeature.query.filter_by(user_id=c.user_id, date=today, feature_key='meeting_hours').first()
                        if r:
                            r.value = float(c.blocked_hours or 0.0)
                    _db.session.commit()

                    # Update tasks_completed_total using ProcessEvent meta old->new
                    start_dt = datetime.combine(today, datetime.min.time())
                    end_dt = datetime.combine(today, datetime.max.time())
                    evs = ProcessEvent.query.filter(
                        and_(ProcessEvent.at >= start_dt, ProcessEvent.at <= end_dt, ProcessEvent.entity=='task', ProcessEvent.event_type=='status_changed')
                    ).all()
                    # Build a set of task completions by assignee users
                    completed_task_ids = []
                    for ev in evs:
                        try:
                            if ev.meta and '->Completed' in ev.meta:
                                completed_task_ids.append(ev.entity_id)
                        except Exception:
                            pass
                    if completed_task_ids:
                        tasks = Task.query.filter(Task.id.in_(completed_task_ids)).all()
                        # credit completions equally to all assignees
                        for t in tasks:
                            for u in t.assignees:
                                rec = UserDailyFeature.query.filter_by(user_id=u.id, date=today, feature_key='tasks_completed_total').first()
                                if rec:
                                    rec.value = (rec.value or 0.0) + 1.0
                        _db.session.commit()
                except Exception:
                    _db.session.rollback()
                time.sleep(3600)  # hourly

    def _nightly_baseline_loop(app_ref):
        from models import UserDailyFeature, UserBehaviorBaseline, db as _db
        from statistics import median
        with app_ref.app_context():
            while True:
                try:
                    # Run at ~02:05 UTC
                    now = datetime.utcnow()
                    if now.hour == 2:
                        span_days = 30
                        cut_date = date.today() - timedelta(days=span_days)
                        # For each user/feature, compute median and MAD; store simple seasonality by weekday for tasks_completed_total
                        feats = UserDailyFeature.query.filter(UserDailyFeature.date >= cut_date).all()
                        by_u_k = {}
                        for f in feats:
                            by_u_k.setdefault((f.user_id, f.feature_key), []).append(float(f.value or 0.0))
                        for (uid, key), vals in by_u_k.items():
                            if not vals:
                                continue
                            c = median(vals)
                            ad = [abs(v - c) for v in vals]
                            mad = median(ad) if ad else 0.0
                            spread = max(1e-6, 1.4826 * mad)
                            row = UserBehaviorBaseline.query.filter_by(user_id=uid, metric_key=key).first()
                            if not row:
                                row = UserBehaviorBaseline(user_id=uid, metric_key=key)
                                _db.session.add(row)
                            row.center = c
                            row.spread = spread
                            if key == 'tasks_completed_total':
                                # compute weekday medians for seasonality
                                per_day = [(r.date, r.value) for r in UserDailyFeature.query.filter_by(user_id=uid, feature_key=key).all()]
                                by_wd = {}
                                for d, v in per_day:
                                    try:
                                        wd = d.weekday()
                                    except Exception:
                                        continue
                                    by_wd.setdefault(wd, []).append(float(v or 0.0))
                                season = {str(k): (median(vs) if vs else 0.0) for k, vs in by_wd.items()}
                                row.seasonality_json = json.dumps({'weekday_median': season})
                            else:
                                row.seasonality_json = None
                            row.updated_at = datetime.utcnow()
                        _db.session.commit()
                    time.sleep(300)  # 5 minutes check window
                except Exception:
                    _db.session.rollback()
                    time.sleep(300)

    # Flask 3: start background jobs once on first request
    app.config.setdefault('BG_THREADS_STARTED', False)
    def _setting_bool(key, default=True):
        try:
            from models import Setting
            s = Setting.query.filter_by(key=key).first()
            if not s or s.value is None:
                return default
            v = str(s.value).strip().lower()
            return v in ('1','true','yes','on')
        except Exception:
            return default
    @app.before_request
    def _ensure_background_jobs():
        if not app.config.get('BG_THREADS_STARTED'):
            try:
                threading.Thread(target=_calendar_capacity_sync_loop, args=(app,), daemon=True).start()
                threading.Thread(target=_ml_skill_updater_loop, args=(app,), daemon=True).start()
                if _setting_bool('reliability_score_enabled', True):
                    threading.Thread(target=_reliability_recompute_loop, args=(app,), daemon=True).start()
                if _setting_bool('anomaly_engine_enabled', True):
                    threading.Thread(target=_integrity_mismatch_detector_loop, args=(app,), daemon=True).start()
                    threading.Thread(target=_after_hours_detector_loop, args=(app,), daemon=True).start()
                    threading.Thread(target=_extreme_deviation_detector_loop, args=(app,), daemon=True).start()
                if _setting_bool('feature_rollups_enabled', True):
                    threading.Thread(target=_hourly_rollup_loop, args=(app,), daemon=True).start()
                if _setting_bool('baseline_refresh_enabled', True):
                    threading.Thread(target=_nightly_baseline_loop, args=(app,), daemon=True).start()
                app.config['BG_THREADS_STARTED'] = True
            except Exception:
                pass

    # Admin: anomalies/reliability pages
    def _require_admin():
        role_name = getattr(getattr(current_user, 'role', None), 'name', None)
        if role_name != 'Admin':
            abort(403)

    @app.route('/admin/anomalies')
    @login_required
    def admin_anomalies():
        _require_admin()
        from models import AnomalyEvent, User
        events = AnomalyEvent.query.order_by(AnomalyEvent.occurred_at.desc()).limit(200).all()
        users_map = {u.id: u for u in User.query.all()}
        return render_template('pages/anomalies.html', events=events, users_map=users_map)

    @app.route('/admin/reliability')
    @login_required
    def admin_reliability():
        _require_admin()
        from models import UserReliabilityScore, User
        rows = UserReliabilityScore.query.order_by(UserReliabilityScore.score.desc()).limit(500).all()
        users_map = {u.id: u for u in User.query.all()}
        return render_template('pages/reliability.html', rows=rows, users_map=users_map)

    @app.route('/admin/investigate/<int:anomaly_id>')
    @login_required
    def admin_investigate(anomaly_id):
        _require_admin()
        from models import AnomalyEvent, User
        ae = AnomalyEvent.query.get_or_404(anomaly_id)
        user = User.query.get(ae.user_id) if ae.user_id else None
        try:
            evidence = json.loads(ae.evidence_json or '{}')
        except Exception:
            evidence = {}
        try:
            explanation = json.loads(ae.explanation_json or '{}')
        except Exception:
            explanation = {}
        return render_template('pages/investigate.html', anomaly=ae, user=user, evidence=evidence, explanation=explanation)

    # Admin JSON APIs
    @app.route('/api/anomalies', methods=['GET'])
    @login_required
    @csrf.exempt
    def api_anomalies_list():
        _require_admin()
        from models import AnomalyEvent
        q = AnomalyEvent.query
        user_id = request.args.get('user_id', type=int)
        if user_id:
            q = q.filter_by(user_id=user_id)
        typ = request.args.get('type')
        if typ:
            q = q.filter_by(type=typ)
        sev = request.args.get('severity')
        if sev:
            q = q.filter_by(severity=sev)
        since = request.args.get('since')
        if since:
            try:
                dt = datetime.fromisoformat(since)
                q = q.filter(AnomalyEvent.occurred_at >= dt)
            except Exception:
                pass
        items = q.order_by(AnomalyEvent.occurred_at.desc()).limit(200).all()
        def row(a):
            return {
                'id': a.id,
                'user_id': a.user_id,
                'severity': a.severity,
                'type': a.type,
                'occurred_at': a.occurred_at.isoformat(),
                'resolved': a.resolved
            }
        return jsonify([row(a) for a in items])

    @app.route('/api/anomalies/<int:aid>', methods=['GET'])
    @login_required
    @csrf.exempt
    def api_anomalies_get(aid):
        _require_admin()
        from models import AnomalyEvent
        a = AnomalyEvent.query.get_or_404(aid)
        return jsonify({
            'id': a.id,
            'user_id': a.user_id,
            'severity': a.severity,
            'type': a.type,
            'occurred_at': a.occurred_at.isoformat(),
            'evidence': json.loads(a.evidence_json or '{}'),
            'explanation': json.loads(a.explanation_json or '{}'),
            'resolved': a.resolved,
        })

    @app.route('/api/anomalies/<int:aid>/resolve', methods=['POST'])
    @login_required
    @csrf.exempt
    def api_anomalies_resolve(aid):
        _require_admin()
        from models import AnomalyEvent, db as _db
        a = AnomalyEvent.query.get_or_404(aid)
        a.resolved = True
        a.resolved_by = current_user.id
        a.resolved_at = datetime.utcnow()
        _db.session.commit()
        return jsonify({'ok': True})

    # ===== My Profile =====
    @app.route('/me/profile', methods=['GET', 'POST'])
    @login_required
    def my_profile():
        from models import UserProfile, UserDailyFeature, UserReliabilityScore, db as _db
        u = current_user
        prof = UserProfile.query.filter_by(user_id=u.id).first()
        if not prof:
            prof = UserProfile(user_id=u.id)
            _db.session.add(prof); _db.session.commit()
        if request.method == 'POST':
            # availability
            av = request.form.get('availability')
            if av:
                u.availability = av
            # profile fields
            prof.job_title = request.form.get('job_title') or prof.job_title
            prof.department = request.form.get('department') or prof.department
            prof.interests = request.form.get('interests') or prof.interests
            skills = request.form.get('skills')  # comma-separated
            if skills is not None:
                try:
                    skill_list = [s.strip() for s in skills.split(',') if s.strip()]
                    prof.skills_json = json.dumps(skill_list)
                except Exception:
                    pass
            prof.updated_at = datetime.utcnow()
            _db.session.commit()
            return redirect(url_for('my_profile'))
        # metrics
        today = date.today()
        last30 = today - timedelta(days=30)
        tasks30 = _db.session.query(UserDailyFeature).filter_by(user_id=u.id, feature_key='tasks_completed_total').filter(UserDailyFeature.date>=last30).all()
        tasks_30d = int(sum(float(r.value or 0.0) for r in tasks30))
        rs = UserReliabilityScore.query.filter_by(user_id=u.id).order_by(UserReliabilityScore.computed_at.desc()).first()
        reliability = rs.score if rs else None
        skills_list = []
        try:
            skills_list = json.loads(prof.skills_json) if prof.skills_json else []
        except Exception:
            pass
        return render_template('pages/profile.html', user=u, prof=prof, tasks_30d=tasks_30d, reliability=reliability, skills_list=skills_list)

    def _require_manager_or_admin():
        role_name = getattr(getattr(current_user, 'role', None), 'name', None)
        if role_name not in ('Admin','Manager','Project Manager'):
            abort(403)

    @app.route('/api/users/pm-candidates', methods=['GET'])
    @login_required
    def api_pm_candidates():
        _require_manager_or_admin()
        from models import User, Role, Project
        p_role = Role.query.filter_by(name='Project Manager').first()
        q = User.query
        if p_role:
            q = q.filter(User.role_id == p_role.id)
        users = q.all()
        res = []
        for uu in users:
            active_projects = Project.query.filter((Project.users.contains(uu)) | (Project.users.any(id=uu.id))).count()
            res.append({
                'id': uu.id,
                'username': uu.username,
                'workload': getattr(uu, 'current_workload', 0.0) or 0.0,
                'active_projects': active_projects
            })
        # sort by workload asc
        res.sort(key=lambda x: x['workload'])
        return jsonify(res)

    @app.route('/api/users/team-candidates', methods=['GET'])
    @login_required
    def api_team_candidates():
        _require_manager_or_admin()
        from models import User, Role, UserProfile, UserDailyFeature
        # parse required skills
        skills_raw = request.args.get('skills','')
        req = [s.strip().lower() for s in (skills_raw.split(',') if skills_raw else []) if s.strip()]
        t_role = Role.query.filter_by(name='Team Member').first()
        q = User.query
        if t_role:
            q = q.filter(User.role_id == t_role.id)
        users = q.all()
        # prefetch features
        today = date.today(); last30 = today - timedelta(days=30)
        feats = UserDailyFeature.query.filter(UserDailyFeature.date>=last30, UserDailyFeature.feature_key=='tasks_completed_total').all()
        tasks30 = {}
        for r in feats:
            tasks30[r.user_id] = tasks30.get(r.user_id, 0.0) + float(r.value or 0.0)
        # profiles
        profs = {p.user_id: p for p in UserProfile.query.all()}
        items = []
        for uu in users:
            av = getattr(uu, 'availability', 'Available')
            if av == 'Out of Office':
                continue
            wl = float(getattr(uu, 'current_workload', 0.0) or 0.0)
            # availability score
            av_score = {'Available':3,'On a Break':2,'In a Meeting':1,'Busy':0}.get(av,0)
            # skills match
            prof = profs.get(uu.id)
            u_skills = []
            try:
                u_skills = json.loads(prof.skills_json) if prof and prof.skills_json else []
            except Exception:
                pass
            u_lower = set(s.lower() for s in u_skills)
            match = 0.0
            if req:
                match = len(set(req) & u_lower) / max(1.0, float(len(req)))
            # workload penalty
            high = 1.0 if wl <= 85.0 else 0.0
            # productivity
            t30 = float(tasks30.get(uu.id, 0.0))
            prod = min(t30/20.0, 1.0)
            rank = (av_score*3.0) + (match*5.0) + (high*2.0) + (prod*2.0)
            items.append({
                'id': uu.id,
                'username': uu.username,
                'availability': av,
                'workload': wl,
                'tasks_done_30d': int(t30),
                'skills': u_skills,
                'rank': rank
            })
        # de-prioritize busy/high-load by sorting rank then workload
        items.sort(key=lambda x: (-x['rank'], x['workload']))
        return jsonify(items[:200])

    # ===== Me & Skills APIs =====
    @app.route('/api/me', methods=['GET'])
    @login_required
    def api_me():
        from models import UserProfile, UserDailyFeature, UserReliabilityScore
        u = current_user
        prof = UserProfile.query.filter_by(user_id=u.id).first()
        skills = []
        try:
            skills = json.loads(getattr(prof, 'skills_json', '') or '[]') if prof else []
        except Exception:
            pass
        today = date.today(); last30 = today - timedelta(days=30)
        feats = UserDailyFeature.query.filter(UserDailyFeature.user_id==u.id, UserDailyFeature.feature_key=='tasks_completed_total', UserDailyFeature.date>=last30).all()
        tasks_30d = int(sum(float(f.value or 0.0) for f in feats))
        rs = UserReliabilityScore.query.filter_by(user_id=u.id).order_by(UserReliabilityScore.computed_at.desc()).first()
        return jsonify({
            'id': u.id,
            'username': u.username,
            'availability': getattr(u,'availability','Available'),
            'current_workload': getattr(u,'current_workload',0.0) or 0.0,
            'tasks_completed_30d': tasks_30d,
            'reliability': rs.score if rs else None,
            'profile': {
                'job_title': getattr(prof,'job_title',None) if prof else None,
                'department': getattr(prof,'department',None) if prof else None,
                'interests': getattr(prof,'interests',None) if prof else None,
                'skills': skills,
            }
        })

    @app.route('/api/me/skills', methods=['POST'])
    @login_required
    @csrf.exempt
    def api_me_skills():
        from models import UserProfile, db as _db
        data = request.get_json(silent=True) or {}
        add = data.get('add') or []
        remove = data.get('remove') or []
        prof = UserProfile.query.filter_by(user_id=current_user.id).first()
        if not prof:
            prof = UserProfile(user_id=current_user.id)
            _db.session.add(prof)
        cur = []
        try:
            cur = json.loads(prof.skills_json or '[]')
        except Exception:
            cur = []
        s = set(x.strip() for x in cur if x and x.strip())
        for a in add:
            if a and isinstance(a, str):
                s.add(a.strip())
        for r in remove:
            if r and isinstance(r, str):
                s.discard(r.strip())
        prof.skills_json = json.dumps(sorted(s))
        prof.updated_at = datetime.utcnow()
        _db.session.commit()
        return jsonify({'skills': sorted(s)})

    @app.route('/api/skills/suggest', methods=['GET'])
    @login_required
    def api_skills_suggest():
        from models import UserSkillHistory
        # Build a simple frequency list from UserSkillHistory plus curated defaults
        curated = [
            'Python','React','Node.js','Go','Java','Kotlin','Swift','C#','SQL','NoSQL',
            'AWS','GCP','Azure','Docker','Kubernetes','Figma','UX Design','UI Design',
            'QA','Cypress','Playwright','Selenium','Data Science','ML','NLP','SEO','Marketing'
        ]
        freq = {}
        try:
            rows = UserSkillHistory.query.all()
            for r in rows:
                k = (r.skill or '').strip()
                if not k:
                    continue
                freq[k] = freq.get(k, 0) + 1
        except Exception:
            pass
        for k in curated:
            freq[k] = max(freq.get(k, 0), 1)
        # optional filter by q
        q = (request.args.get('q') or '').strip().lower()
        items = [{'skill': k, 'count': v} for k, v in freq.items() if not q or q in k.lower()]
        items.sort((lambda a, b: -1 if a['count']>b['count'] else (1 if a['count']<b['count'] else ( -1 if a['skill']<b['skill'] else 1))))
        # Fallback: Pythonic sort
        items = sorted(items, key=lambda x: (-x['count'], x['skill']))
        return jsonify(items[:50])

    # ===== Ingestor APIs (Admin only) =====
    def _require_admin_or_abort():
        role_name = getattr(getattr(current_user, 'role', None), 'name', None)
        if role_name != 'Admin':
            abort(403)

    @app.route('/api/ingest/vcs', methods=['POST'])
    @login_required
    @csrf.exempt
    def api_ingest_vcs():
        _require_admin_or_abort()
        from models import UserDailyFeature, ProcessEvent, db as _db
        payload = request.get_json(force=True) or {}
        uid = int(payload.get('user_id'))
        d = payload.get('date') or date.today().isoformat()
        the_date = date.fromisoformat(d)
        commits = float(payload.get('commits_count', 0))
        pr_opened = int(payload.get('pr_opened', 0))
        pr_merged = int(payload.get('pr_merged', 0))
        for k, v in [('commits_count', commits)]:
            rec = UserDailyFeature.query.filter_by(user_id=uid, date=the_date, feature_key=k).first()
            if not rec:
                rec = UserDailyFeature(user_id=uid, date=the_date, feature_key=k, value=0.0, source='vcs')
                _db.session.add(rec)
            rec.value = float(v)
        # process events for PRs
        for _ in range(pr_opened):
            _db.session.add(ProcessEvent(source='vcs', entity='pull_request', entity_id=0, event_type='opened', meta=f'user={uid}', at=datetime.utcnow()))
        for _ in range(pr_merged):
            _db.session.add(ProcessEvent(source='vcs', entity='pull_request', entity_id=0, event_type='merged', meta=f'user={uid}', at=datetime.utcnow()))
        _db.session.commit()
        return jsonify({'ok': True})

    @app.route('/api/ingest/calendar', methods=['POST'])
    @login_required
    @csrf.exempt
    def api_ingest_calendar():
        _require_admin_or_abort()
        from models import UserCapacity, UserDailyFeature, db as _db
        payload = request.get_json(force=True) or {}
        uid = int(payload.get('user_id'))
        d = payload.get('date') or date.today().isoformat()
        the_date = date.fromisoformat(d)
        meeting_hours = float(payload.get('meeting_hours', 0))
        blocked_hours = float(payload.get('blocked_hours', meeting_hours))
        cap = UserCapacity.query.filter_by(user_id=uid, date=the_date).first()
        if not cap:
            cap = UserCapacity(user_id=uid, date=the_date, source='calendar')
            _db.session.add(cap)
        cap.blocked_hours = blocked_hours
        # write meeting_hours feature
        rec = UserDailyFeature.query.filter_by(user_id=uid, date=the_date, feature_key='meeting_hours').first()
        if not rec:
            rec = UserDailyFeature(user_id=uid, date=the_date, feature_key='meeting_hours', value=0.0, source='calendar')
            _db.session.add(rec)
        rec.value = meeting_hours
        _db.session.commit()
        return jsonify({'ok': True})

    @app.route('/api/ingest/time', methods=['POST'])
    @login_required
    @csrf.exempt
    def api_ingest_time():
        _require_admin_or_abort()
        from models import UserDailyFeature, db as _db
        payload = request.get_json(force=True) or {}
        uid = int(payload.get('user_id'))
        d = payload.get('date') or date.today().isoformat()
        the_date = date.fromisoformat(d)
        coding = float(payload.get('time_logged_coding_hours', 0))
        total = float(payload.get('time_logged_total_hours', coding))
        for k, v in [('time_logged_coding_hours', coding), ('time_logged_total_hours', total)]:
            rec = UserDailyFeature.query.filter_by(user_id=uid, date=the_date, feature_key=k).first()
            if not rec:
                rec = UserDailyFeature(user_id=uid, date=the_date, feature_key=k, value=0.0, source='time')
                _db.session.add(rec)
            rec.value = float(v)
        _db.session.commit()
        return jsonify({'ok': True})

    @app.route('/files/download/<int:project_id>/<path:filename>')
    @login_required
    @require_roles('Admin')
    def files_download(project_id, filename):
        import os
        upload_root = os.path.join(app.root_path, 'uploads')
        project_dir = os.path.join(upload_root, str(project_id))
        if not os.path.isfile(os.path.join(project_dir, filename)):
            abort(404)
        # Audit log
        try:
            from models import AuditLog
            db.session.add(AuditLog(
                actor_id=current_user.id,
                action='download_file',
                target_type='project',
                target_id=project_id,
                meta=filename
            ))
            db.session.commit()
        except Exception:
            pass
        return send_from_directory(project_dir, filename, as_attachment=True)

    @app.route('/files/delete', methods=['POST'])
    @login_required
    @require_roles('Admin')
    def files_delete():
        import os
        pid = request.form.get('project_id', type=int)
        filename = request.form.get('filename')
        if not pid or not filename:
            abort(400)
        upload_root = os.path.join(app.root_path, 'uploads')
        project_dir = os.path.join(upload_root, str(pid))
        file_path = os.path.join(project_dir, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception:
            pass
        # Audit log
        try:
            from models import AuditLog
            db.session.add(AuditLog(
                actor_id=current_user.id,
                action='delete_file',
                target_type='project',
                target_id=pid,
                meta=filename
            ))
            db.session.commit()
        except Exception:
            pass
        return redirect(url_for('files', project_id=pid))

    # Admin: manage users and roles
    @app.route('/admin/users', methods=['GET', 'POST'])
    @login_required
    @require_roles('Admin')
    def admin_users():
        from models import User, Role, AuditLog
        if request.method == 'POST':
            action = request.form.get('action')
            user_id = request.form.get('user_id', type=int)
            user = User.query.get_or_404(user_id)
            if action == 'set_role':
                role_name = request.form.get('role')
                role = Role.query.filter_by(name=role_name).first()
                if role:
                    user.role = role
                    db.session.commit()
                    # audit
                    try:
                        db.session.add(AuditLog(
                            actor_id=current_user.id,
                            action='set_role',
                            target_type='user',
                            target_id=user.id,
                            meta=role.name
                        ))
                        db.session.commit()
                    except Exception:
                        pass
            elif action == 'reset_password':
                new_pw = request.form.get('new_password') or 'ChangeMe@123'
                user.set_password(new_pw)
                db.session.commit()
                # audit
                try:
                    db.session.add(AuditLog(
                        actor_id=current_user.id,
                        action='reset_password',
                        target_type='user',
                        target_id=user.id
                    ))
                    db.session.commit()
                except Exception:
                    pass
            return redirect(url_for('admin_users'))

        # Filters
        q = request.args.get('q', '').strip()
        role_filter = request.args.get('role', '').strip()
        query = User.query
        if q:
            query = query.filter((User.username.ilike(f'%{q}%')) | (User.email.ilike(f'%{q}%')))
        if role_filter:
            query = query.join(Role, isouter=True).filter(Role.name == role_filter)
        users = query.order_by(User.username).all()
        roles = Role.query.order_by(Role.name).all()
        return render_template('admin/users.html', users=users, roles=roles)

    # Admin: audit viewer
    @app.route('/admin/audit')
    @login_required
    @require_roles('Admin')
    def admin_audit():
        from models import AuditLog, User
        from sqlalchemy import desc
        from datetime import datetime, timedelta
        action = request.args.get('action', '').strip()
        actor = request.args.get('actor', '').strip()
        days = request.args.get('days', type=int) or 30
        since = datetime.utcnow() - timedelta(days=days)

        q = AuditLog.query.join(User, AuditLog.actor_id == User.id, isouter=True).filter(AuditLog.created_at >= since)
        if action:
            q = q.filter(AuditLog.action == action)
        if actor:
            q = q.filter(User.username.ilike(f'%{actor}%'))
        logs = q.order_by(desc(AuditLog.created_at)).limit(200).all()
        actions = ['upload_file','download_file','delete_file','set_role','reset_password','export_csv']
        return render_template('admin/audit.html', logs=logs, actions=actions)

    return app

# Optional: for direct run (but usually use `flask run`)
if __name__ == "__main__":
    app = create_app()
    app.run()