from app import create_app
from models import db, User, Role

app = create_app()
with app.app_context():
    db.create_all()  # ensure tables incl. Role exist

    role = Role.query.filter_by(name='Admin').first()
    if not role:
        role = Role(name='Admin', description='System administrator')
        db.session.add(role)
        db.session.commit()

    u = User.query.filter_by(username='admin').first()
    if not u:
        u = User(username='admin', email='admin@example.com')
        u.set_password('admin@123')
        u.role = role
        db.session.add(u)
    else:
        u.role = role

    db.session.commit()
    print("Admin seeded:", u.username, u.email, "role:", u.role.name)
