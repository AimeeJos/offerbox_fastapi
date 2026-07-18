# Update user details after registration
from fastapi import Query
import random
import os
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
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta

router = APIRouter()




def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

def get_otp_expiry(minutes=5):
    return datetime.utcnow() + timedelta(minutes=minutes)

async def send_otp(email: str, otp: str):
    # Placeholder for actual SMS/email sending logic
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    from_email = "aimeemary15@gmail.com"
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    server.login(from_email, EMAIL_PASSWORD)  # Use your email password or app password
    
    msg = EmailMessage()
    msg.set_content(f"Your OTP is: {otp}")
    msg['Subject'] = "Your OTP"
    msg['From'] = from_email
    msg['To'] = email
    server.send_message(msg)

    print(f"Sending OTP {otp} to {email}")
    # Integrate with SMS/email provider here
    return True



# Register or login with email: generates and sends OTP
@router.post("/register-or-login")
async def register_or_login(email: str = Body(..., embed=True), name: str = Body(..., embed=True), user_type: str = Body(..., embed=True)):
    user = await db["users"].find_one({"emailaddress": email})
    if user_type not in ["user", "admin", "shop"]:
        raise HTTPException(status_code=400, detail="Invalid user type")
    if not user:
        # Register new user with only email
        await db["users"].insert_one({
            "_id": str(uuid4()),
            "emailaddress": email,
            "username": name,
            "hashed_password": "",
            "is_login": False,
            "user_type":user_type,
            "coins":120,
            "used_passcodes":[]
            })
    otp = generate_otp()
    expiry = get_otp_expiry()
    _ = await db["otp_codes"].insert_one({
        "emailaddress": email,
        "otp": otp,
        "expiry": expiry,
        "is_verified": False
    })
    _ = await send_otp(email, otp)
    return {"msg": "OTP sent to your email address", "otp": otp}





# OTP Verification: issues tokens if OTP is valid
@router.post("/verify-otp")
async def verify_otp(emailaddress: str = Body(...), otp: str = Body(...)):
    otp_record = await db["otp_codes"].find_one({
        "emailaddress": emailaddress,
        "otp": otp,
        "is_verified": False
    })
    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid OTP or email address")
    if datetime.utcnow() > otp_record["expiry"]:
        raise HTTPException(status_code=400, detail="OTP expired")
    await db["otp_codes"].update_one({"_id": otp_record["_id"]}, {"$set": {"is_verified": True}})
    user = await db["users"].find_one({"emailaddress": emailaddress})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_update = await db["users"].update_one({"_id": user["_id"]}, {"$set": {"is_login": True}})
    access_token = create_access_token({"sub": user["emailaddress"]})
    refresh_token = create_refresh_token({"sub": user["emailaddress"]})
    return {
        "user_type": user["user_type"],
        "name": user["username"],
        "coins": user["coins"],
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/home")
async def home(emailaddress: str = Body(..., embed=True)):
    user = await db["users"].find_one({"emailaddress": emailaddress})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "username": user.get("username"),
        "coins": user.get("coins", 0),
    }


@router.post("/refresh")
async def refresh_token(refresh_token: str = Body(..., embed=True)):
    payload = decode_token(refresh_token)
    if payload is None or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    emailaddress = payload["sub"]
    user = await db["users"].find_one({"emailaddress": emailaddress})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    access_token = create_access_token({"sub": emailaddress})
    return {"access_token": access_token, "token_type": "bearer"}
