from fastapi import APIRouter, Depends, Body
from core.database import db
from core.auth import get_current_user

router = APIRouter()

@router.post("/offers")
async def create_offers(
    payload: dict = Body(...),
    # current_user: dict = Depends(get_current_user)
    ):
    # convert payload to dict to store in database
    offer_data = dict(payload)
    # store offer in database
    _ = await db["offers"].insert_one(offer_data)
    
    return payload

@router.get("/offers")
async def read_offers():
    offers = [offer async for offer in db["offers"].find()]
    print(offers)
    return {"offers": offers}

# get request by id
@router.get("/offers/{offer_id}")
async def read_offer(offer_id: str):
    offer = await db["offers"].find_one({"_id": offer_id})
    if not offer:
        return {"msg": "Offer not found"}
    return offer

# update offer by id
@router.put("/offers/{offer_id}")
async def update_offer(offer_id: str, payload: dict = Body(...)):
    offer_data = dict(payload)
    result = await db["offers"].update_one({"_id": offer_id}, {"$set": offer_data})
    if result.matched_count == 0:
        return {"msg": "Offer not found"}
    return {"msg": "Offer updated successfully"}

# delete offer by id
@router.delete("/offers/{offer_id}")
async def delete_offer(offer_id: str):
    result = await db["offers"].delete_one({"_id": offer_id})
    if result.deleted_count == 0:
        return {"msg": "Offer not found"}
    return {"msg": "Offer deleted successfully"}