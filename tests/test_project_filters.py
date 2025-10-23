from datetime import date, timedelta
from models import db, User, Project, Task


def login(client, username, password):
    return client.post('/login', data={'username': username, 'password': password}, follow_redirects=False)


def seed_data(app):
    with app.app_context():
        u = User(username='filteruser', email='filteruser@example.com')
        u.set_password('pw123456')
        db.session.add(u)
        p1 = Project(title='P with Done task', deadline=date.today()+timedelta(days=5))
        p2 = Project(title='P overdue', deadline=date.today()-timedelta(days=1))
        db.session.add_all([p1, p2]); db.session.commit()
        t1 = Task(title='done', status='Done', project=p1)
        t2 = Task(title='todo', status='To Do', project=p2)
        db.session.add_all([t1, t2]); db.session.commit()
        p1.users.append(u); db.session.commit()
        return u


def test_projects_filters_status_assignee_deadline(client, app):
    u = seed_data(app)

    # login
    resp = login(client, 'filteruser', 'pw123456')
    assert resp.status_code in (302, 303)

    # status=Done -> should include P with Done task
    resp = client.get('/projects/?status=Done')
    assert resp.status_code == 200
    assert b'P with Done task' in resp.data

    # assignee filter -> projects where user is assigned
    resp = client.get(f'/projects/?assignee={u.id}')
    assert resp.status_code == 200
    assert b'P with Done task' in resp.data and b'P overdue' not in resp.data

    # deadline filter -> only deadlines <= given date (today)
    resp = client.get(f'/projects/?deadline={date.today().isoformat()}')
    assert resp.status_code == 200
    assert b'P overdue' in resp.data and b'P with Done task' not in resp.data
