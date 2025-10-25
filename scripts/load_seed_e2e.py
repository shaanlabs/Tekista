import argparse
import json
import os
import sys
from pathlib import Path

import requests

# Ensure project root on sys.path so 'app' and 'models' can be imported
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Defer importing app/models until needed to avoid ModuleNotFoundError in API-only mode
# We'll bind these globals when entering DB/API paths.
create_app = None
db = None
User = None
Role = None
Project = None
Task = None


def ensure_role(session, name: str):
    r = Role.query.filter_by(name=name).first()
    if not r:
        r = Role(name=name)
        session.add(r)
        session.commit()
    return r


def upsert_user(session, u):
    email = u["email"]
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(username=u["name"], email=email, password_hash="")
        session.add(user)
        session.commit()
    # role
    role_name = (
        "Admin"
        if u["role"] == "Admin"
        else ("Manager" if u["role"] in ("Manager", "Project Manager") else "Member")
    )
    role = ensure_role(session, role_name)
    user.role_id = role.id
    # availability & workload if present
    if "availability_status" in u:
        user.availability = u["availability_status"]
    if "current_workload" in u:
        try:
            user.current_workload = float(u["current_workload"])
        except Exception:
            pass
    session.commit()
    return user


def upsert_project(session, p):
    title = p["projectName"]
    proj = Project.query.filter_by(title=title).first()
    if not proj:
        proj = Project(title=title, description="")
        session.add(proj)
        session.commit()
    return proj


def api_token(base, username, password):
    resp = requests.post(
        f"{base}/api/token",
        json={"username": username, "password": password},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["token"]


def api_upsert_project(base, token, p):
    # Try to find by title first
    resp = requests.get(
        f"{base}/api/projects", headers={"Authorization": f"Bearer {token}"}, timeout=15
    )
    resp.raise_for_status()
    exists = next((x for x in resp.json() if x["title"] == p["projectName"]), None)
    if exists:
        return exists["id"]
    resp = requests.post(
        f"{base}/api/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": p["projectName"], "description": ""},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def api_create_task(base, token, t):
    resp = requests.post(
        f"{base}/api/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json=t,
        timeout=15,
    )
    resp.raise_for_status()
    created = resp.json()
    # Patch status if provided and not default
    if t.get("status") and t["status"] != created.get("status"):
        rid = created["id"]
        r2 = requests.patch(
            f"{base}/api/tasks/{rid}",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": t["status"]},
            timeout=15,
        )
        r2.raise_for_status()
        created = r2.json()
    return created["id"]


def main():
    ap = argparse.ArgumentParser(
        description="Load seed E2E JSON into app (API or DB modes)"
    )
    ap.add_argument("--mode", choices=["api", "db"], default="api")
    ap.add_argument("--file", default=str(Path("data") / "seed_e2e_full.json"))
    ap.add_argument("--base", default="http://127.0.0.1:5000")
    ap.add_argument("--admin-username")
    ap.add_argument("--admin-password")
    ap.add_argument(
        "--skip-users",
        action="store_true",
        help="[Deprecated] Same as --no-upsert-users",
    )
    ap.add_argument(
        "--no-upsert-users",
        action="store_true",
        help="API mode: do not upsert users via DB (requires users to already exist)",
    )
    args = ap.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"Seed file not found: {path}", file=sys.stderr)
        sys.exit(1)

    seed = json.loads(path.read_text(encoding="utf-8"))

    if args.mode == "db":
        # Import app/models only in DB mode
        from app import create_app as _create_app
        from models import Project as _Project
        from models import Role as _Role
        from models import Task as _Task
        from models import User as _User
        from models import db as _db

        # Bind globals so helpers like ensure_role/upsert_user see proper classes
        global User, Role, Project, Task, db
        User, Role, Project, Task, db = _User, _Role, _Project, _Task, _db
        app = _create_app()
        ctx = app.app_context()
        ctx.push()
        created_u = updated_u = 0
        for u in seed.get("users", []):
            existed = _User.query.filter_by(email=u["email"]).first() is not None
            upsert_user(_db.session, u)
            if existed:
                updated_u += 1
            else:
                created_u += 1
        created_p = updated_p = 0
        for p in seed.get("projects", []):
            existed = (
                _Project.query.filter_by(title=p["projectName"]).first() is not None
            )
            upsert_project(_db.session, p)
            if existed:
                updated_p += 1
            else:
                created_p += 1
        created_t = 0
        for t in seed.get("tasks", []):
            proj = (
                _Project.query.filter_by(id=t["projectId"]).first()
                or _Project.query.filter_by(title=f"Project {t['projectId']}").first()
            )
            if not proj:
                continue
            # avoid duplicate by title+project
            existing = _Task.query.filter_by(
                title=t["taskTitle"], project_id=proj.id
            ).first()
            if existing:
                continue
            new_t = _Task(
                title=t["taskTitle"],
                description="",
                priority=t.get("priority", "Medium"),
                project_id=proj.id,
                status=t.get("status", "To-Do"),
            )
            _db.session.add(new_t)
            _db.session.commit()
            created_t += 1
        print(
            f"DB mode: users created={created_u}, updated={updated_u}; projects created={created_p}, updated={updated_p}; tasks created={created_t}"
        )
        return

    # API mode
    if not (args.skip_users or args.no_upsert_users):
        # Import app/models to upsert users before API calls
        from app import create_app as _create_app
        from models import Role as _Role
        from models import User as _User
        from models import db as _db

        global User, Role, db
        User, Role, db = _User, _Role, _db
        app = _create_app()
        ctx = app.app_context()
        ctx.push()
        for u in seed.get("users", []):
            upsert_user(_db.session, u)
    # login for API
    if not args.admin_username or not args.admin_password:
        print(
            "Provide --admin-username and --admin-password for API mode",
            file=sys.stderr,
        )
        sys.exit(2)
    token = api_token(args.base, args.admin_username, args.admin_password)

    # Map: email->id for assignments
    # users_map not required; tasks payload uses user IDs directly when present
    # Projects
    project_id_map = {}
    for p in seed.get("projects", []):
        pid = api_upsert_project(args.base, token, p)
        project_id_map[p["projectId"]] = pid
    # Tasks
    created_t = 0
    for t in seed.get("tasks", []):
        pid = project_id_map.get(t["projectId"]) or t["projectId"]
        payload = {
            "title": t["taskTitle"],
            "project_id": pid,
            "priority": t.get("priority", "Medium"),
            "assignees": [t["assigned_to"]] if t.get("assigned_to") else [],
            "estimated_hours": 4.0,
        }
        if t.get("status"):
            payload["status"] = t["status"]  # will be patched after create
        api_create_task(args.base, token, payload)
        created_t += 1
    print(
        f"API mode: users upserted via DB={len(seed.get('users', [])) if not args.skip_users else 0}; projects upserted={len(project_id_map)}; tasks created={created_t}"
    )


if __name__ == "__main__":
    main()
