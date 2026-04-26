# Update user details after registration
from fastapi import Query
import random

from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from core.auth import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    decode_token,
)
from core.database import db
from models.user import User
from uuid import uuid4
import random
import string
from datetime import datetime, timedelta

router = APIRouter()




def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

def get_otp_expiry(minutes=5):
    return datetime.utcnow() + timedelta(minutes=minutes)

async def send_otp(phonenumber: str, otp: str):
    # Placeholder for actual SMS/email sending logic
    print(f"Sending OTP {otp} to {phonenumber}")
    # Integrate with SMS/email provider here
    return True



# Register or login with phone number: generates and sends OTP
@router.post("/register-or-login")
async def register_or_login(phonenumber: str = Body(..., embed=True)):
    user = await db["users"].find_one({"phonenumber": phonenumber})
    if not user:
        # Register new user with only phone number
        user = User(phonenumber=phonenumber, username=phonenumber, hashed_password="", fullname="", emailaddress="")
        await db["users"].insert_one({"_id": str(uuid4()), "phonenumber": phonenumber})
    otp = generate_otp()
    expiry = get_otp_expiry()
    _ = await db["otp_codes"].insert_one({
        "phonenumber": phonenumber,
        "otp": otp,
        "expiry": expiry,
        "used": False
    })
    _ = await send_otp(phonenumber, otp)
    return {"msg": "OTP sent to your phone number"}





# OTP Verification: issues tokens if OTP is valid
@router.post("/verify-otp")
async def verify_otp(phonenumber: str = Body(...), otp: str = Body(...)):
    otp_record = await db["otp_codes"].find_one({
        "phonenumber": phonenumber,
        "otp": otp,
        "used": False
    })
    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid OTP or phone number")
    if datetime.utcnow() > otp_record["expiry"]:
        raise HTTPException(status_code=400, detail="OTP expired")
    await db["otp_codes"].update_one({"_id": otp_record["_id"]}, {"$set": {"used": True}})
    user = await db["users"].find_one({"phonenumber": phonenumber})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    access_token = create_access_token({"sub": user["phonenumber"]})
    refresh_token = create_refresh_token({"sub": user["phonenumber"]})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


# Update user details endpoint
@router.post("/register")
async def update_user_details(
    phonenumber: str = Body(...),
    username: str = Body(...),
    place: str = Body(...),
    age: int = Body(...),
    gender: str = Body(...)
):
    user = await db["users"].find_one({"phonenumber": phonenumber})
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please register/login with your phone number first.")
    random_number = random.randint(1000, 9999)
    user_id = f"{username}#{random_number}"
    update_fields = {
        "username": username,
        "place": place,
        "age": age,
        "gender": gender,
        "user_id": user_id
    }
    await db["users"].update_one({"phonenumber": phonenumber}, {"$set": update_fields})
    return {"msg": "User details updated successfully", "user_id": user_id}

@router.post("/refresh")
async def refresh_token(refresh_token: str = Body(..., embed=True)):
    payload = decode_token(refresh_token)
    if payload is None or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    username = payload["sub"]
    user = await db["users"].find_one({"username": username})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    access_token = create_access_token({"sub": username})
    return {"access_token": access_token, "token_type": "bearer"}
