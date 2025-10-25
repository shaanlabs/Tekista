from app import create_app
from models import Role, User, db

app = create_app()
with app.app_context():
    db.create_all()
    role = Role.query.filter_by(name='Admin').first()
    if not role:
        role = Role(name='Admin', description='System administrator')
        db.session.add(role); db.session.commit()
    u = User.query.filter_by(username='admin').first()
    if not u:
        u = User(username='admin', email='admin@example.com')
        db.session.add(u)
    u.set_password('admin@123')
    u.role = role
    db.session.commit()
    print('Admin reset:', u.username, 'role:', u.role.name)
