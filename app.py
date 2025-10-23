# app.py
from flask import Flask, render_template, session, jsonify, request
from flask_login import LoginManager, login_required, current_user
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect, generate_csrf
import os
import sys
import logging
from functools import wraps


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

    # register blueprint at root so routes like /login are available
    # (previously registered with url_prefix='/auth' which caused 404s for /login)
    app.register_blueprint(auth_bp)  # removed url_prefix='/auth'

    app.register_blueprint(projects_bp, url_prefix="/projects")
    app.register_blueprint(tasks_bp, url_prefix="/tasks")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(ai_bp, url_prefix="/ai")
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

    # Add index route -> use new dashboard as the home page
    @app.route('/')
    @login_required
    def index():
        return render_template('dashboard.html')
    
    # Enterprise dashboard removed

    return app

# Optional: for direct run (but usually use `flask run`)
if __name__ == "__main__":
    app = create_app()
    app.run()