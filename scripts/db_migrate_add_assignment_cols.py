from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app import create_app
from models import db

app = create_app()
with app.app_context():
    conn = db.engine.connect()

    def add_col(table, coldef):
        try:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {coldef}"))
            print("added", table, coldef)
        except SQLAlchemyError as err:
            print("skip", table, coldef, "-", err)

    add_col("user", "current_workload FLOAT DEFAULT 0")
    add_col("user", 'availability VARCHAR(20) DEFAULT "Available"')
    add_col("task", "estimated_hours FLOAT DEFAULT 4.0")

    try:
        conn.execute(
            text("UPDATE user SET current_workload=0 WHERE current_workload IS NULL")
        )
    except SQLAlchemyError as err:
        print("seed workload skip", err)
    try:
        conn.execute(
            text(
                'UPDATE user SET availability="Available" WHERE availability IS NULL OR availability=""'
            )
        )
    except SQLAlchemyError as err:
        print("seed availability skip", err)
    try:
        conn.execute(
            text("UPDATE task SET estimated_hours=4.0 WHERE estimated_hours IS NULL")
        )
    except SQLAlchemyError as err:
        print("seed estimated skip", err)

    print("migration done")
