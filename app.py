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
        return User.query.get(int(user_id))

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