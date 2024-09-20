from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import controllers

from .libs import sql_alchemy_lib

from fastapi.staticfiles import StaticFiles

import os


"""
This user to auto create all table
"""

"""
INIT ALL Database Here
"""

app = FastAPI()


app.include_router(controllers.user_router.router)

origins = [
    "http://localhost",
    "http://localhost:3000",
    "https://tools.slingacademy.com",
    "https://www.slingacademy.com",
    "https://amimumherbalproject.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=['*'],
)


root_directory = os.getcwd()  # Gets the current working directory
images_directory = os.path.join(root_directory, "images")
app.mount("/images", StaticFiles(directory=images_directory), name="images")
