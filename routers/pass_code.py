from datetime import datetime
from fastapi import APIRouter, Depends, Body
from core.database import db
from core.auth import get_current_user
from utilities.random_utility import UniqueRandomGenerator

router = APIRouter()

# get request by id
@router.get("/passcode/{passcode_id}")
async def read_passcode(passcode_id: str):
    passcode = await db["passcodes"].find_one({"passcode_id": passcode_id}, {"_id": 0})
    
    if not passcode:
        return {"error": "Passcode not found"}
    return passcode

# create passcode

# {
#   "pass_code":"NMNM555",
# "description":"food context",
# "is_expired":false,
# "no_of_coins":100
# }

@router.post("/passcode")
async def create_passcode(payload: dict = Body(...)):
    # convert payload to dict to store in database
    passcode_data = dict(payload)
    # validate that the passcode_id is unique
    existing_passcode = await db["passcodes"].find_one({"pass_code": passcode_data["pass_code"]})
    if existing_passcode:
        return {"error": "Passcode already exists"}
    # store passcode in database
    _ = await db["passcodes"].insert_one(passcode_data)
    
    return payload

# delete passcode by id
@router.delete("/passcode/{passcode_id}")
async def delete_passcode(passcode_id: str):
    result = await db["passcodes"].delete_one({"passcode_id": passcode_id})
    if result.deleted_count == 0:
        return {"error": "Passcode not found"}
    return {"msg": "Passcode deleted successfully"}


# update passcode by id
@router.put("/passcode/{passcode_id}")
async def update_passcode(passcode_id: str, payload: dict = Body(...)):
    passcode_data = dict(payload)
    # validate that the passcode exists before updating
    existing_passcode = await db["passcodes"].find_one({"passcode_id": passcode_id})
    if not existing_passcode:
        return {"error": "Passcode not found"}
    
    result = await db["passcodes"].update_one({"passcode_id": passcode_id}, {"$set": passcode_data})
    if result.matched_count == 0:
        return {"error": "Passcode not found"}
    return {"msg": "Passcode updated successfully"}


# get all passcodes
@router.get("/passcodes")
async def read_passcodes():
    passcodes = [passcode async for passcode in db["passcodes"].find({}, {"_id": 0})]
    return {"passcodes": passcodes}


# verify passcode
@router.post("/coins/redeem")
async def verify_passcode(passcode: str = Body(...), user_email: str = Body(...)):
    passcode_record = await db["passcodes"].find_one({"pass_code": passcode})
    if not passcode_record:
        return {"error": "Invalid passcode"}
    # fetch user from database
    user = await db["users"].find_one({"emailaddress": user_email})
    if not user:
        return {"error": "User not found"}
    # check if passcode has already been used by the user
    if passcode in user.get("used_passcodes", []):
        return {"error": "Passcode has already been used by this user"}
    
    total_coins = user.get("coins", 0) + passcode_record.get("no_of_coins", 0)
    # update user's coins and add passcode to used_passcodes
    _ = await db["users"].update_one({"emailaddress": user_email}, {"$set": {"coins": total_coins}, "$push": {"used_passcodes": passcode}})
    return {
        "status": "success",
        "addedCoins": passcode_record.get("no_of_coins", 0),
        "totalCoins": total_coins
        }


