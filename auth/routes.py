from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user

from models import User, db

from . import auth_bp
# import forms (added)
from .forms import LoginForm, RegisterForm


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter(
            (User.username == form.username.data) | (User.email == form.email.data)
        ).first():
            flash("Username or email already exists", "warning")
        else:
            u = User(username=form.username.data, email=form.email.data)
            u.set_password(form.password.data)
            db.session.add(u)
            db.session.commit()
            flash("Account created. Please log in.", "success")
            return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get("next") or url_for("projects.list_projects")
            return redirect(next_page)
        flash("Invalid credentials", "danger")
    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """
    Simple forgot-password endpoint. On POST accept an 'email' field and flash a neutral message.
    Replace the TODO with your password-reset token/email sending implementation.
    """
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        # TODO: look up user and send password reset email if registered
        flash(
            "If that email is registered, you will receive password reset instructions shortly.",
            "info",
        )
        # Redirect to login or another appropriate page
        return redirect(url_for("auth.login"))
    # Render a template at templates/auth/forgot_password.html (create if missing)
    return render_template("auth/forgot_password.html")
