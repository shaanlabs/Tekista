from models import db, User, Project, Task
from datetime import date, timedelta


def get_token_with_data(client, app):
    with app.app_context():
        u = User(username='metrics', email='metrics@example.com')
        u.set_password('pw123456')
        db.session.add(u)
        p = Project(title='Analytic P')
        db.session.add(p); db.session.commit()
        db.session.add_all([
            Task(title='T done', status='Done', project=p, due_date=date.today()-timedelta(days=1)),
            Task(title='T todo', status='To Do', project=p, due_date=date.today()+timedelta(days=2)),
        ])
        db.session.commit()
    resp = client.post('/api/token', json={'username': 'metrics', 'password': 'pw123456'})
    return resp.get_json()['token']


def H(token):
    return {'Authorization': f'Bearer {token}'}


def test_api_metrics_endpoints(client, app):
    token = get_token_with_data(client, app)

    # metrics
    r = client.get('/api/analytics/metrics', headers=H(token))
    assert r.status_code == 200 and 'projects' in r.get_json()

    # performance
    r = client.get('/api/analytics/performance', headers=H(token))
    assert r.status_code == 200 and isinstance(r.get_json(), list)

    # activity
    r = client.get('/api/activity', headers=H(token))
    assert r.status_code == 200 and isinstance(r.get_json(), list)

    # project analytics
    with app.app_context():
        pid = Project.query.first().id
    r = client.get(f'/api/projects/{pid}/analytics', headers=H(token))
    assert r.status_code == 200 and 'project' in r.get_json()

    # report generation
    r = client.post('/api/reports/generate', headers=H(token), json={'type': 'project', 'project_id': pid})
    assert r.status_code == 200 and r.headers.get('Content-Type') == 'text/csv'
