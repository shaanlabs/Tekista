
from models import Project, User, db


def get_token(client, app):
    with app.app_context():
        u = User(username="apiuser", email="apiuser@example.com")
        u.set_password("pw123456")
        db.session.add(u)
        db.session.commit()
    resp = client.post(
        "/api/token", json={"username": "apiuser", "password": "pw123456"}
    )
    assert resp.status_code == 200
    return resp.get_json()["token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_api_projects_crud(client, app):
    token = get_token(client, app)

    # Create
    resp = client.post(
        "/api/projects",
        headers=auth_headers(token),
        json={"title": "API Project", "description": "d"},
    )
    assert resp.status_code == 201
    pid = resp.get_json()["id"]

    # Read list
    resp = client.get("/api/projects", headers=auth_headers(token))
    assert resp.status_code == 200 and any(p["id"] == pid for p in resp.get_json())

    # Update
    resp = client.patch(
        f"/api/projects/{pid}",
        headers=auth_headers(token),
        json={"description": "updated"},
    )
    assert resp.status_code == 200 and resp.get_json()["description"] == "updated"

    # Delete
    resp = client.delete(f"/api/projects/{pid}", headers=auth_headers(token))
    assert resp.status_code == 204


def test_api_tasks_crud(client, app):
    token = get_token(client, app)
    # seed project
    with app.app_context():
        p = Project(title="P1")
        db.session.add(p)
        db.session.commit()
        pid = p.id

    # Create
    resp = client.post(
        "/api/tasks",
        headers=auth_headers(token),
        json={"title": "T1", "project_id": pid},
    )
    assert resp.status_code == 201
    tid = resp.get_json()["id"]

    # Read
    resp = client.get(f"/api/tasks/{tid}", headers=auth_headers(token))
    assert resp.status_code == 200 and resp.get_json()["title"] == "T1"

    # Update
    resp = client.patch(
        f"/api/tasks/{tid}", headers=auth_headers(token), json={"status": "Done"}
    )
    assert resp.status_code == 200 and resp.get_json()["status"] == "Done"

    # Delete
    resp = client.delete(f"/api/tasks/{tid}", headers=auth_headers(token))
    assert resp.status_code == 204
