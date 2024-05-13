import users
import upload_images.detect as detect
import upload_images.identify as identify
import upload_images.search as search

import admin
from fastapi import FastAPI


app = FastAPI()


app.include_router(users.router)
app.include_router(detect.router)
app.include_router(identify.router)
app.include_router(search.router)
app.include_router(admin.router)
