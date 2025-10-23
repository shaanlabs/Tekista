from models import db, User, Project


def login(client, username, password):
    return client.post('/login', data={'username': username, 'password': password}, follow_redirects=False)


def setup_user_project(app):
    from models import User, Project
    with app.app_context():
        u = User(username='tasker', email='tasker@example.com')
        u.set_password('pw123456')
        p = Project(title='Tasks Project')
        db.session.add_all([u, p]); db.session.commit()
        return u, p


def test_tasks_create_global_validation_and_success(client, app):
    u, p = setup_user_project(app)
    resp = login(client, 'tasker', 'pw123456')
    assert resp.status_code in (302, 303)

    # Missing title -> validation message, 200
    resp = client.post('/tasks/create', data={'project_id': p.id}, follow_redirects=True)
    assert resp.status_code == 200

    # Valid create -> redirect to task detail
    resp = client.post('/tasks/create', data={
        'title': 'New Task',
        'project_id': p.id,
        'priority': 'High'
    }, follow_redirects=False)
    assert resp.status_code in (302, 303)
