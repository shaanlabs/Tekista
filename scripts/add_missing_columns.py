import os
import sys

# Ensure project root is on sys.path so `app` and `models` can be imported when running from scripts/
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import text

from app import create_app
from models import db

"""
One-off SQLite migration script to add missing columns introduced in models.py
- user.organization_id (INTEGER)
- user.role_id (INTEGER)
- user.custom_role_id (INTEGER)
- project.organization_id (INTEGER)

Run:  python scripts/add_missing_columns.py
"""

def add_column_if_missing(table: str, column: str, coltype: str):
    cols = {row[1] for row in db.session.execute(text(f"PRAGMA table_info({table})")).fetchall()}
    if column not in cols:
        db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}"))
        print(f"Added {table}.{column}")
    else:
        print(f"Column {table}.{column} already exists")


def main():
    app = create_app()
    with app.app_context():
        add_column_if_missing('user', 'organization_id', 'INTEGER')
        add_column_if_missing('user', 'role_id', 'INTEGER')
        add_column_if_missing('user', 'custom_role_id', 'INTEGER')
        add_column_if_missing('project', 'organization_id', 'INTEGER')
        # API analytics selects Task.created_at; ensure it exists
        add_column_if_missing('task', 'created_at', 'DATETIME')
        # Task schema used by queries/templates
        add_column_if_missing('task', 'parent_id', 'INTEGER')
        add_column_if_missing('task', 'recurrence_rule', 'TEXT')
        add_column_if_missing('task', 'recurrence_end', 'DATE')
        add_column_if_missing('task', 'is_template', 'BOOLEAN')
        add_column_if_missing('task', 'template_name', 'VARCHAR(120)')
        db.session.commit()
        print('Done')


if __name__ == '__main__':
    main()
