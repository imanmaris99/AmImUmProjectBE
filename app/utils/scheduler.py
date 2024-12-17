# app/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from app.services.user_services import delete_unverified_users
from app.libs.sql_alchemy_lib import get_db  # Menggunakan dependency get_db

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=delete_unverified_users, 
        trigger='interval', 
        days=1, 
        args=[next(get_db())]  # Mengambil session menggunakan dependency get_db
    )
    scheduler.start()
    return scheduler


# from apscheduler.schedulers.background import BackgroundScheduler
# from app.libs.sql_alchemy_lib import session_local
# from app.services.user_services import delete_unverified_users

# def start_scheduler():
#     scheduler = BackgroundScheduler()
#     scheduler.add_job(
#         delete_unverified_users, 
#         'interval', 
#         minutes=5, 
#         args=[session_local()]
#     )
#     scheduler.start()
#     return scheduler
