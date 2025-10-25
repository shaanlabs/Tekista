from models import Role, User, db


def login(client, username, password):
    return client.post('/login', data={'username': username, 'password': password}, follow_redirects=False)


def ensure_admin(app):
    with app.app_context():
        admin_role = Role.query.filter_by(name='Admin').first()
        if not admin_role:
            admin_role = Role(name='Admin')
            db.session.add(admin_role); db.session.commit()
        user = User(username='adminuser', email='adminuser@example.com')
        user.set_password('pw123456')
        user.role = admin_role
        db.session.add(user); db.session.commit()
        non = User(username='plain', email='plain@example.com')
        non.set_password('pw123456')
        db.session.add(non); db.session.commit()
        return user, non


def test_reports_access_control(client, app):
    admin, non = ensure_admin(app)

    # non-admin -> 403
    resp = login(client, 'plain', 'pw123456')
    assert resp.status_code in (302, 303)
    resp = client.get('/reports')
    assert resp.status_code == 403

    # admin -> 200
    client.get('/logout')
    resp = login(client, 'adminuser', 'pw123456')
    assert resp.status_code in (302, 303)
    resp = client.get('/reports')
    assert resp.status_code == 200
