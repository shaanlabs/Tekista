from functools import wraps
from flask import request, g, jsonify
from flask_login import current_user
from models import User

def api_auth_required(f):
	"""Decorator that allows Authorization via token or existing session login."""
	@wraps(f)
	def decorated(*args, **kwargs):
		# Check Authorization header first
		auth = request.headers.get('Authorization', None)
		user = None
		if auth:
			parts = auth.split()
			# Accept formats: "Token <token>" or "Bearer <token>"
			if len(parts) == 2 and parts[0].lower() in ('token', 'bearer'):
				token = parts[1]
				user = User.verify_api_token(token)
		# Fall back to session user
		if user is None and current_user and current_user.is_authenticated:
			user = current_user
		if user is None:
			return jsonify({'error':'unauthorized'}), 401
		g.api_user = user
		return f(*args, **kwargs)
	return decorated
