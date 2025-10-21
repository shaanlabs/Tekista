# app.py
from flask import Flask, render_template, jsonify
from flask_login import LoginManager, login_required, current_user
from flask_mail import Mail
import os
import sys
import logging
from functools import wraps


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, User
from config import Config

# Initialize extensions (using the SAME db from models.py)
login_manager = LoginManager()
login_manager.login_view = "auth.login"
mail = Mail()

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

    # Register blueprints
    from auth.routes import auth_bp
    from projects.routes import projects_bp
    from tasks.routes import tasks_bp
    from api.routes import api_bp
    from ai.routes import aibp as ai_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(projects_bp, url_prefix="/projects")
    app.register_blueprint(tasks_bp, url_prefix="/tasks")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(ai_bp, url_prefix="/ai")

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

    # Add index route
    @app.route('/')
    def index():
        return render_template('index.html', 
                            ai_enabled=app.config.get('ENABLE_AI_FEATURES', False))
    
    # Add enterprise dashboard route
    @app.route('/enterprise')
    @login_required
    def enterprise_dashboard():
        return render_template('enterprise_dashboard.html')

    return app

# Optional: for direct run (but usually use `flask run`)
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)