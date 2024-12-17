from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy import Engine
import os
from dotenv import load_dotenv

load_dotenv()
"""
#######################This use to create connection with database###########################################
"""
APP_DEVELOPMENT = os.getenv("APP_DEVELOPMENT", True)
engine: Engine

SQLALCHEMY_DATABASE_URL = os.getenv('DATABASE_URL')
# engine = create_engine(
#     SQLALCHEMY_DATABASE_URL,
#     pool_pre_ping=True
#     )
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # Memeriksa koneksi sebelum digunakan
    pool_size=5,         # Maksimal 5 koneksi
    max_overflow=10,     # Koneksi tambahan jika pool penuh
    pool_recycle=1800    # Recycle koneksi setelah 30 menit
)

"""
######################Tis code use to make interact with database object###################################
######################Mostly to do manipulation to define entity of database###############################
"""
session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
"""
#########################Base is abstract object use to define table on database############################
#########################Developer will use it as abstract object to inherit################################
"""
Base = declarative_base()
"""
############################This code use to get the session, use to manipulation data######################
############################How to use the code,should by fastapi way#######################################
############################How to use it have something to do with dependency injection####################
############################To understand more about the code please read de fastapi document###############
############################Read this [https://fastapi.tiangolo.com/tutorial/sql-databases/]################
"""


# Dependency to get the database session
def get_db():
    database = session_local()
    try:
        yield database
    finally:
        database.close()
