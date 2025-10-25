import os
import sys
from getpass import getpass

# Ensure project root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models import Role, User, db


def main():
    username = os.environ.get("ADMIN_USERNAME") or "admin_1"
    email = os.environ.get("ADMIN_EMAIL") or f"{username}@tekista.com"
    password = os.environ.get("ADMIN_PASSWORD")
    if not password:
        # prompt if not provided
        try:
            password = getpass("Enter password for admin user: ")
        except (EOFError, KeyboardInterrupt):
            print(
                "Set ADMIN_PASSWORD env var or run interactively to input password.",
                file=sys.stderr,
            )
            sys.exit(2)

    app = create_app()
    ctx = app.app_context()
    ctx.push()

    role = Role.query.filter_by(name="Admin").first()
    if not role:
        role = Role(name="Admin", description="Full system access")
        db.session.add(role)
        db.session.commit()

    user = User.query.filter_by(username=username).first()
    created = False
    if not user:
        user = User(username=username, email=email, role_id=role.id)
        created = True
        db.session.add(user)
    user.role_id = role.id
    user.set_password(password)
    db.session.commit()

    print(
        ("Created" if created else "Updated")
        + f" admin user '{username}' with email '{email}'."
    )


if __name__ == "__main__":
    main()
