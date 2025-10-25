from flask import url_for

from models import Project, db


def login(client, username, password):
    return client.post('/login', data={
        'username': username,
        'password': password,
        'remember': 'y'
    }, follow_redirects=False)


def test_index_redirects_when_anonymous(client):
    resp = client.get('/', follow_redirects=False)
    assert resp.status_code in (301, 302, 303)


def test_login_flow(client, app, user):
    # GET login page
    resp = client.get('/login')
    assert resp.status_code == 200
    # POST credentials
    resp = login(client, 'tester', 'testpass123')
    # Should redirect after login
    assert resp.status_code in (302, 303)


def test_projects_requires_auth(client):
    resp = client.get('/projects/', follow_redirects=False)
    # should redirect to login
    assert resp.status_code in (301, 302, 303)


def test_projects_list_after_login(client, app, user):
    # login
    resp = login(client, 'tester', 'testpass123')
    assert resp.status_code in (302, 303)

    # index now requires login and should return 200 after auth
    resp = client.get('/')
    assert resp.status_code == 200

    # seed a project
    with app.app_context():
        p = Project(title='Test Project', description='Desc')
        db.session.add(p)
        db.session.commit()

    # visit list
    resp = client.get('/projects/')
    assert resp.status_code == 200
    assert b'Test Project' in resp.data
