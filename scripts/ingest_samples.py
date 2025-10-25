from datetime import date, datetime

from app import create_app
from models import ProcessEvent, Setting, UserCapacity, UserDailyFeature, db

# Configure here
USER_ID = 21  # adjust to an existing Member ID
THE_DATE = date.today()

app = create_app()
ctx = app.app_context()
ctx.push()

# Ensure feature flags
for k in ['anomaly_engine_enabled','reliability_score_enabled','feature_rollups_enabled','baseline_refresh_enabled']:
    if not Setting.query.filter_by(key=k).first():
        db.session.add(Setting(key=k, value='true'))

db.session.commit()

# Time tracking: coding=7h, total=8h
for k, v in [('time_logged_coding_hours', 7.0), ('time_logged_total_hours', 8.0)]:
    rec = UserDailyFeature.query.filter_by(user_id=USER_ID, date=THE_DATE, feature_key=k).first()
    if not rec:
        rec = UserDailyFeature(user_id=USER_ID, date=THE_DATE, feature_key=k, value=0.0, source='time')
        db.session.add(rec)
    rec.value = float(v)

db.session.commit()

# VCS: commits_count=0; PR opened=0, merged=0; also write a PR event to test feed
rec = UserDailyFeature.query.filter_by(user_id=USER_ID, date=THE_DATE, feature_key='commits_count').first()
if not rec:
    rec = UserDailyFeature(user_id=USER_ID, date=THE_DATE, feature_key='commits_count', value=0.0, source='vcs')
    db.session.add(rec)
rec.value = 0.0
# optional PR events
db.session.add(ProcessEvent(source='vcs', entity='pull_request', entity_id=0, event_type='opened', meta=f'user={USER_ID}', at=datetime.utcnow()))

db.session.commit()

# Calendar: meeting_hours=3.0, blocked_hours=3.0
cap = UserCapacity.query.filter_by(user_id=USER_ID, date=THE_DATE).first()
if not cap:
    cap = UserCapacity(user_id=USER_ID, date=THE_DATE, source='calendar')
    db.session.add(cap)
cap.blocked_hours = 3.0
rec = UserDailyFeature.query.filter_by(user_id=USER_ID, date=THE_DATE, feature_key='meeting_hours').first()
if not rec:
    rec = UserDailyFeature(user_id=USER_ID, date=THE_DATE, feature_key='meeting_hours', value=0.0, source='calendar')
    db.session.add(rec)
rec.value = 3.0

db.session.commit()

print('Ingested sample features for user', USER_ID, 'on', THE_DATE)
print('Anomaly detectors will evaluate within 10-15 minutes; check /admin/anomalies or GET /api/anomalies?user_id=', USER_ID)
