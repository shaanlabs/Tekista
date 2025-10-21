import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
	SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
	SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or \
		"sqlite:///" + os.path.join(basedir, "app.db")
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	
	# Mail configuration
	MAIL_SERVER = os.environ.get('MAIL_SERVER', 'localhost')
	MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
	MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
	MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
	MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
	MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@taskmanager.com')
	
	# App configuration
	APP_BASE_URL = os.environ.get('APP_BASE_URL', 'http://localhost:5000')
	
	# AI Configuration
	OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
	ENABLE_AI_FEATURES = os.environ.get('ENABLE_AI_FEATURES', 'false').lower() in ['true', 'on', '1']
	
	# AI Model Settings
	AI_MODEL = os.environ.get('AI_MODEL', 'gpt-3.5-turbo')
	AI_TEMPERATURE = float(os.environ.get('AI_TEMPERATURE', '0.7'))
	AI_MAX_TOKENS = int(os.environ.get('AI_MAX_TOKENS', '500'))
