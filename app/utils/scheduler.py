from apscheduler.schedulers.background import BackgroundScheduler
from app.libs.sql_alchemy_lib import session_local
from app.services.user_services import delete_unverified_users

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(delete_unverified_users, 'interval', minutes=1, args=[session_local()])
    scheduler.start()
    return scheduler
