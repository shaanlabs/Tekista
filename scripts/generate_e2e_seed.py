import csv
import json
import random
from datetime import date, datetime, timedelta
from pathlib import Path

random.seed(42)

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Distributions
AVAIL_BUCKETS = (
    ("Available", 0.60),
    ("Busy", 0.20),
    ("In a Meeting", 0.10),
    ("Out of Office", 0.10),
)
SKILL_POOL = [
    "Python","React","Node.js","Go","Java","Kotlin","Swift","C#","SQL","NoSQL",
    "AWS","GCP","Azure","Docker","Kubernetes","Figma","UX Design","UI Design",
    "QA","Cypress","Playwright","Selenium","Data Science","ML","NLP","SEO","Marketing",
]

# Helpers

def pick_availability():
    r = random.random()
    acc = 0.0
    for name, p in AVAIL_BUCKETS:
        acc += p
        if r <= acc:
            return name
    return AVAIL_BUCKETS[-1][0]


def pick_skills(k=None):
    k = k or random.randint(2, 4)
    return random.sample(SKILL_POOL, k)


def make_users():
    users = []
    uid = 1
    # 5 Admins
    for i in range(5):
        users.append({
            "userId": uid,
            "name": f"Admin {i+1}",
            "email": f"admin{i+1}@example.com",
            "role": "Admin",
            "availability_status": pick_availability(),
            "current_workload": random.randint(5, 60),
            "skills": []
        })
        uid += 1
    # 15 Managers
    for i in range(15):
        users.append({
            "userId": uid,
            "name": f"PM {i+1}",
            "email": f"pm{i+1}@example.com",
            "role": "Manager",
            "availability_status": pick_availability(),
            "current_workload": random.randint(10, 70),
            "skills": []
        })
        uid += 1
    # 55 Members with skills
    for i in range(55):
        users.append({
            "userId": uid,
            "name": f"Member {i+1}",
            "email": f"member{i+1}@example.com",
            "role": "Member",
            "availability_status": pick_availability(),
            "current_workload": random.randint(0, 95),
            "skills": pick_skills(),
        })
        uid += 1
    return users


def make_projects(managers):
    projects = []
    for i in range(15):
        status = random.choices(["Active","Paused","Completed"],[0.7,0.1,0.2])[0]
        projects.append({
            "projectId": i+1,
            "projectName": f"Project {chr(65+i)}",  # A..O
            "projectManagerId": random.choice(managers)["userId"],
            "status": status
        })
    return projects


def find_candidates(users, required_skills):
    rs = set(required_skills)
    cands = [u for u in users if u["role"] == "Member" and rs.issubset(set(u.get("skills", [])))]
    return cands


def choose_assignee(cands):
    if not cands:
        return None
    # Prefer Available and lower workload
    cands = sorted(cands, key=lambda u: (u["availability_status"] != "Available", u["current_workload"]))
    return cands[0]


def make_tasks(projects, users):
    tasks = []
    project_ids = [p["projectId"] for p in projects]

    def new_task(tid, base_status, assigned):
        pid = random.choice(project_ids)
        prio = random.choices(["Low","Medium","High"],[0.2,0.5,0.3])[0]
        req = random.sample(SKILL_POOL, random.randint(1,2))
        assignee = None
        if assigned:
            cands = find_candidates(users, req)
            assignee = choose_assignee(cands) or random.choice([u for u in users if u["role"]=="Member"])  # fall back
        status = base_status
        if status == "Overdue":
            # Mark as To-Do but overdue flag separate; keeping status for test coverage
            pass
        due_offset = random.randint(-10, 15)
        due_date = (date.today() + timedelta(days=due_offset)).isoformat()
        return {
            "taskId": tid,
            "taskTitle": f"Task {tid}",
            "projectId": pid,
            "priority": prio,
            "required_skills": req,
            "status": status,
            "assigned_to": assignee["userId"] if assignee else None,
            "due_date": due_date
        }

    tid = 1
    # 50 To-Do unassigned
    for _ in range(50):
        tasks.append(new_task(tid, "To-Do", assigned=False)); tid += 1
    # 50 To-Do assigned
    for _ in range(50):
        tasks.append(new_task(tid, "To-Do", assigned=True)); tid += 1
    # 50 In-Progress assigned
    for _ in range(50):
        tasks.append(new_task(tid, "In-Progress", assigned=True)); tid += 1
    # 25 Completed assigned
    for _ in range(25):
        tasks.append(new_task(tid, "Completed", assigned=True)); tid += 1
    # 25 Overdue assigned
    for _ in range(25):
        t = new_task(tid, "Overdue", assigned=True)
        # ensure overdue due_date in past
        t["due_date"] = (date.today() - timedelta(days=random.randint(1, 10))).isoformat()
        tasks.append(t); tid += 1

    return tasks


def write_seed(users, projects, tasks, path):
    payload = {
        "users": users,
        "projects": projects,
        "tasks": tasks,
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)


def write_plan_csv(path):
    headers = [
        "Test Case ID","User Role","Feature","Test Steps","Expected Result","Actual Result"
    ]
    rows = []
    # A. Admin & User Management
    rows += [
        ["TC-001","Admin","User Login","Go to /login, enter admin creds, click Login","Dashboard loads without error",""],
        ["TC-002","Admin","Create User","Go to Users, click Add User, fill form (Member), Save","New user appears in list",""],
        ["TC-003","Admin","Read User","Go to Users list, search by email","User row visible with correct role",""],
        ["TC-004","Admin","Update User","Open user, change role to Manager, Save","User role shows Manager",""],
        ["TC-005","Admin","Delete User","Delete a user who has In-Progress tasks","User deleted or blocked with clear message",""],
        ["TC-006","Admin","Delete User - E2E","Check tasks of deleted user","Tasks become Unassigned or reassigned per policy",""],
    ]
    # B. Project Manager & Manual Task Workflow
    rows += [
        ["TC-007","Manager","Create Project","Go to Projects, New Project, assign PM, Save","Project created and visible",""],
        ["TC-008","Manager","Create Task","Open project, New Task, fill fields, Save","Task appears in project backlog",""],
        ["TC-009","Manager","Manual Assignment","Assign the task to an Available Member","Task shows assigned_to user",""],
        ["TC-010","Manager","View Workload","Open Team dashboard","All team members and workloads visible",""],
        ["TC-011","Manager","View Availability","Open availability dashboard","Only Available users listed",""],
    ]
    # C. Team Member Workflow
    rows += [
        ["TC-012","Member","View My Tasks","Login as assigned member; open My Tasks","Task from TC-009 is visible",""],
        ["TC-013","Member","Start Task","Open task; change status To-Do -> In-Progress","Task shows In-Progress",""],
        ["TC-014","Manager","Check Workload","Login as PM; open Team dashboard","Member now appears Busy / workload increased",""],
        ["TC-015","Member","Complete Task","Change status In-Progress -> Completed","Task shows Completed; workload decreased",""],
        ["TC-016","Member","Change Availability","Open profile; set status to Out of Office","Availability updated to Out of Office",""],
    ]
    # D. Core AI Automation Engine
    rows += [
        ["TC-017","Manager","Trigger AI","Create High Priority task with required_skills ['Python','React'] and no assignee","Task queued for auto-assignment",""],
        ["TC-018","Manager","AI Logic - Skills","Wait/refresh; check task assignee","Assigned to member with Python & React",""],
        ["TC-019","Manager","AI Logic - Availability","Confirm an OOO member with Python & React did NOT get task","OOO member did not receive task",""],
        ["TC-020","Manager","AI Logic - Workload","Find two Available members with skills (20% vs 90% workload); create similar task","Assigned to 20% workload member",""],
        ["TC-021","Manager","AI - E2E Feedback","Check PM dashboard after assignment","Task removed from unassigned; assignee workload increased",""],
    ]
    # E. Negative & Error Testing
    rows += [
        ["TC-022","Manager","Validation Error","Create task without title and submit","Validation error 'Title is required' shown; task not created",""],
        ["TC-023","Member","Permissions Error","As Member, try to create a project","Permission denied or control hidden",""],
        ["TC-024","Manager","Data Mismatch","Assign a task to an Out of Office user","Warning shown: 'This user is currently Out of Office. Are you sure?'",""],
    ]

    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)


def main():
    users = make_users()
    managers = [u for u in users if u["role"] == "Manager"]
    projects = make_projects(managers)
    tasks = make_tasks(projects, users)

    seed_path = DATA_DIR / 'seed_e2e_full.json'
    plan_path = DATA_DIR / 'e2e_test_plan.csv'

    write_seed(users, projects, tasks, seed_path)
    write_plan_csv(plan_path)

    print(f"Wrote {seed_path}")
    print(f"Wrote {plan_path}")


if __name__ == '__main__':
    main()
