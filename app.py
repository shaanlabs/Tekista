from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
mail = Mail()

def create_app():
	from config import Config
	app = Flask(__name__, template_folder="templates")
	app.config.from_object(Config)

	db.init_app(app)
	login_manager.init_app(app)
	mail.init_app(app)

	# register blueprints
	from auth.routes import auth_bp
	from projects.routes import projects_bp
	from tasks.routes import tasks_bp
	from api.routes import api_bp

	app.register_blueprint(auth_bp)
	app.register_blueprint(projects_bp, url_prefix="/projects")
	app.register_blueprint(tasks_bp, url_prefix="/tasks")
	app.register_blueprint(api_bp, url_prefix="/api")

	return app

# If run directly, create app for quick scripts
if __name__ == "__main__":
	app = create_app()
	from projects import projects_bp
	app.register_blueprint(projects_bp, url_prefix='/projects')
	app.run(debug=True)
