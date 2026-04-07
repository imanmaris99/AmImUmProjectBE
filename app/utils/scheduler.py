from apscheduler.schedulers.background import BackgroundScheduler

from app.libs.sql_alchemy_lib import session_local
from app.services.user_services import delete_unverified_users

scheduler = None


def _cleanup_unverified_users():
    db = session_local()
    try:
        delete_unverified_users(db)
    finally:
        db.close()


def start_scheduler():
    global scheduler

    if scheduler is not None:
        return scheduler

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=_cleanup_unverified_users,
        trigger='interval',
        days=1,
        id='cleanup_unverified_users',
        replace_existing=True,
    )
    scheduler.start()
    return scheduler
