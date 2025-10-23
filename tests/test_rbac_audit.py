import io
import re
from flask import url_for
from models import db, User, Role, Project, Task, AuditLog


def ensure_roles(app):
    with app.app_context():
        admin = Role.query.filter_by(name='Admin').first()
        if not admin:
            admin = Role(name='Admin', description='Administrator')
            db.session.add(admin)
            db.session.commit()
        member = Role.query.filter_by(name='Member').first()
        if not member:
            member = Role(name='Member', description='Member')
            db.session.add(member)
            db.session.commit()
        return admin, member


def make_user(username, email, password, role):
    u = User(username=username, email=email)
    u.set_password(password)
    u.role = role
    db.session.add(u)
    db.session.commit()
    return u


def login(client, username, password):
    return client.post('/login', data={'username': username, 'password': password}, follow_redirects=False)


def test_csv_export_rbac_and_audit(client, app):
    admin_role, member_role = ensure_roles(app)
    with app.app_context():
        # seed users
        admin = make_user('admin_test', 'admin_test@example.com', 'pw123456', admin_role)
        member = make_user('member_test', 'member_test@example.com', 'pw123456', member_role)
        # seed project and a task
        p = Project(title='RBAC Project', description='desc')
        db.session.add(p); db.session.commit()
        t = Task(title='T1', project=p)
        db.session.add(t); db.session.commit()

    # member login: expect 403
    resp = login(client, 'member_test', 'pw123456')
    assert resp.status_code in (302, 303)
    resp = client.get(f'/projects/{p.id}/export')
    assert resp.status_code == 403

    # admin login: expect CSV and audit log write
    resp = client.get('/logout', follow_redirects=False)
    assert resp.status_code in (302, 303)
    resp = login(client, 'admin_test', 'pw123456')
    assert resp.status_code in (302, 303)

    resp = client.get(f'/projects/{p.id}/export')
    assert resp.status_code == 200
    assert resp.headers.get('Content-Disposition', '').startswith('attachment;')

    with app.app_context():
        entry = AuditLog.query.filter_by(action='export_csv', target_id=p.id).order_by(AuditLog.id.desc()).first()
        assert entry is not None


def test_files_upload_delete_audit(client, app, tmp_path):
    admin_role, _ = ensure_roles(app)
    with app.app_context():
        admin = make_user('file_admin', 'file_admin@example.com', 'pw123456', admin_role)
        p = Project(title='Files Project')
        db.session.add(p); db.session.commit()
        pid = p.id

    # login as admin
    resp = login(client, 'file_admin', 'pw123456')
    assert resp.status_code in (302, 303)

    # upload
    data = {
        'project_id': str(pid),
        'file': (io.BytesIO(b'hello'), 'hello.txt')
    }
    resp = client.post('/files/upload', data=data, content_type='multipart/form-data')
    assert resp.status_code in (302, 303)

    # delete
    resp = client.post('/files/delete', data={'project_id': str(pid), 'filename': 'hello.txt'})
    assert resp.status_code in (302, 303)

    with app.app_context():
        up = AuditLog.query.filter_by(action='upload_file', target_id=pid).first()
        de = AuditLog.query.filter_by(action='delete_file', target_id=pid).first()
        assert up is not None and de is not None


def test_admin_users_filters(client, app):
    admin_role, member_role = ensure_roles(app)
    with app.app_context():
        # seed data
        admin = make_user('admin_filter', 'admin_filter@example.com', 'pw123456', admin_role)
        make_user('alpha', 'alpha@example.com', 'pw123456', member_role)
        make_user('beta', 'beta@example.com', 'pw123456', member_role)

    # login as admin
    resp = login(client, 'admin_filter', 'pw123456')
    assert resp.status_code in (302, 303)

    # filter by q
    resp = client.get('/admin/users?q=alpha')
    assert resp.status_code == 200
    assert b'alpha@example.com' in resp.data
    assert b'beta@example.com' not in resp.data

    # filter by role
    resp = client.get('/admin/users?role=Member')
    assert resp.status_code == 200
    assert b'alpha@example.com' in resp.data and b'beta@example.com' in resp.data
    assert b'admin_filter@example.com' not in resp.data
