Brief note about mail config and the new API/export features.

Mail configuration (optional)
- To enable email notifications set these environment variables or add to config.py:
  MAIL_SERVER, MAIL_PORT, MAIL_USE_TLS/MAIL_USE_SSL, MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER
- Example (env):
  set MAIL_SERVER=smtp.example.com
  set MAIL_PORT=587
  set MAIL_USE_TLS=1
  set MAIL_USERNAME=you@example.com
  set MAIL_PASSWORD=secret
  set MAIL_DEFAULT_SENDER=you@example.com

API endpoints
- GET /api/projects
- GET /api/projects/<id>
- GET /api/tasks
- POST /api/tasks  (JSON: { "title": "...", "project_id": 1, "assignees":[1,2], "description": "..."} )

Export
- Use the project export: GET /projects/<project_id>/export to download tasks CSV.

Comments
- You can add comments on a task on the task detail page.

Run and DB creation: ...existing code...