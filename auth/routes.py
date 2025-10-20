from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from . import auth_bp
from .forms import RegisterForm, LoginForm
from models import User

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
	form = RegisterForm()
	if form.validate_on_submit():
		if User.query.filter((User.username==form.username.data)|(User.email==form.email.data)).first():
			flash('Username or email already exists', 'warning')
		else:
			u = User(username=form.username.data, email=form.email.data)
			u.set_password(form.password.data)
			db.session.add(u); db.session.commit()
			flash('Account created. Please log in.', 'success')
			return redirect(url_for('auth.login'))
	return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(username=form.username.data).first()
		if user and user.check_password(form.password.data):
			login_user(user)
			next_page = request.args.get('next') or url_for('projects.list_projects')
			return redirect(next_page)
		flash('Invalid credentials', 'danger')
	return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('auth.login'))
