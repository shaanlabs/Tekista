from app import create_app
from models import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    conn = db.engine.connect()

    def add_col(table, coldef):
        try:
            conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {coldef}'))
            print('added', table, coldef)
        except Exception as e:
            print('skip', table, coldef, '-', e)

    add_col('user', 'current_workload FLOAT DEFAULT 0')
    add_col('user', 'availability VARCHAR(20) DEFAULT \"Available\"')
    add_col('task', 'estimated_hours FLOAT DEFAULT 4.0')

    try: conn.execute(text('UPDATE user SET current_workload=0 WHERE current_workload IS NULL'))
    except Exception as e: print('seed workload skip', e)
    try: conn.execute(text('UPDATE user SET availability=\"Available\" WHERE availability IS NULL OR availability=\"\"'))
    except Exception as e: print('seed availability skip', e)
    try: conn.execute(text('UPDATE task SET estimated_hours=4.0 WHERE estimated_hours IS NULL'))
    except Exception as e: print('seed estimated skip', e)

    print('migration done')
