from fastapi import FastAPI
from routers import auth, offers, users

app = FastAPI()

app.include_router(auth.router)
app.include_router(offers.router)
app.include_router(users.router)
