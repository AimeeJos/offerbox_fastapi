from fastapi import Body
from fastapi import APIRouter, Depends
from core.database import db
from typing import List
from models.user import User
from core.auth import get_current_user
# Route to fetch a particular user by id
from fastapi import HTTPException
from uuid import UUID


router = APIRouter()


@router.get("/users")
async def list_users(current_user: dict = Depends(get_current_user)):
    print(f"Current user: {current_user}")
    users_cursor = db["users"].find({}, {"_id": 1, "username": 1, "emailaddress": 1, "is_login": 1})
    users = await users_cursor.to_list(length=100)
    print(f"Fetched users: {users}")
    return users

