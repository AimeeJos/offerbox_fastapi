from fastapi import FastAPI
from routers import auth, offers, pass_code, users

app = FastAPI()

app.include_router(auth.router)
app.include_router(offers.router)
app.include_router(users.router)
app.include_router(pass_code.router)

