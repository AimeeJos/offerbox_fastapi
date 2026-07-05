from datetime import datetime
import random
from fastapi import APIRouter, Depends, Body, HTTPException
from core.database import db
from core.auth import get_current_user
from utilities.random_utility import UniqueRandomGenerator

router = APIRouter()

@router.post("/offers")
async def create_offers(payload: dict = Body(...),
    # current_user: dict = Depends(get_current_user)
    ):
    
        #     {
        # "offer_id": "c1b2f7c0-8c3a-4f2e-9a3c-9d6e5a8b1234",
        # "shop_id": "84dd1f88-63d3-4246-a960-e6887c1ebcb1",
        # "offer_name": "Summer Mega Sale",
        # "description": "Get up to 50% off on selected products.",
        # "contest_id": "SUMMER50",
        # "is_active": true,
        
        # "question": "What is the capital of France?"
        # "options": ["Paris", "London", "Berlin", "Madrid"],
        # "correct_answer": "Paris",

        # "validity_start_date": "2026-06-21T00:00:00Z",
        # "validity_end_date": "2026-07-31T23:59:59Z",
        # "valid_no_of_offer":"10",
        
        # "coins_required": 100,


        # "created_by": "admin",
        # "created_at": "2026-06-21T10:00:00Z",
        # "updated_at": "2026-06-21T10:00:00Z"

        # }
    
    # convert payload to dict to store in database
    offer_data = dict(payload)
    won_ranks=[]
    generator = UniqueRandomGenerator(1, 100)

    for _ in range(10):
        won_ranks.append(generator.get_number())
        
    offer_data["won_ranks"] = won_ranks
    # store offer in database
    _ = await db["offers"].insert_one(offer_data)
    
    return payload

@router.get("/offers")
async def read_offers():
    offers = [offer async for offer in db["offers"].find({}, {"_id": 0})]
    print(offers)
    return {"offers": offers}

# get request by id
@router.get("/offers/{offer_id}")
async def read_offer(offer_id: str):
    offer = await db["offers"].find_one({"offer_id": offer_id}, {"_id": 0})
    offer.pop("won_ranks", None)
    if not offer:
        return {"msg": "Offer not found"}
    return offer

# update offer by id
@router.put("/offers/{offer_id}")
async def update_offer(offer_id: str, payload: dict = Body(...)):
    offer_data = dict(payload)
    result = await db["offers"].update_one({"offer_id": offer_id}, {"$set": offer_data})
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



# @router.post("/register")
# async def register_user(promo_code: str = Body(...), emailaddress: str = Body(...)):
#     # fetch offer by promo code
#     offer = await db["offers"].find_one({"promo_code": promo_code}, {"_id": 0})
#     print(f"Fetched offer: {offer}")
#     # fetch user by email address
#     user = await db["users"].find_one({"emailaddress": emailaddress}, {"_id": 0})
#     print(f"Fetched user: {user}")
    
#     # check how manyth offer is being registered for the promo code
#     registration_count = await db["registrations"].count_documents({"promo_code": promo_code})
#     print(f"Current registration count for promo code {promo_code}: {registration_count}")
#     # update qr_code_generated field in offer document
#     qr_code_generated = registration_count+1
#     _ = await db["offers"].update_one({"promo_code": promo_code}, {"$set": {"qr_code_generated": qr_code_generated}})
    
#     offer_status = "LOST"
#     won_ranks = offer.get("won_ranks", [])
#     print(f"Won ranks for offer {offer['offer_id']}: {won_ranks}")
#     if qr_code_generated in won_ranks:
#         offer_status = "WON"
#     # create registration record
#     registration_data = {
#         "emailaddress": emailaddress,
#         "promo_code": promo_code,
#         "offer_id": offer["offer_id"],
#         "shop_id": offer["shop_id"],
#         "registration_date": datetime.utcnow(),
#         "status": "REGISTERED",
#         "rank": qr_code_generated,
#         "offer_status": offer_status
#     }
#     _ = await db["registrations"].insert_one(registration_data)
    
    

# Submit lucky-draw answer
@router.post("/lucky-draw/participate")
async def submit_answer(contestId: str = Body(...), answer: str = Body(...), email_address: str = Body(...)):
    # fetch offer by contestId
    offer = await db["offers"].find_one({"contest_id": contestId}, {"_id": 0})
    if not offer:
        return {"status": "Invalid code"}
    # check if answer is correct
    if str(answer).lower() != str(offer["correct_answer"]).lower():
        return {"status": "Sorry, Better luck next time!"}
    # check if user has enough coins to participate
    coins_required = offer.get("coins_required", 0)
    user = await db["users"].find_one({"emailaddress": email_address}, {"_id": 0})
    if not user:
        return {"status": "User not found"}
    
    user_coins = user.get("coins", 0)
    if user_coins < coins_required:
        return {"status": "out of coins", "remaining_coins": user_coins, "coins_required": coins_required}
    
    # fetch rank of last user who registered for the contest
    last_registration = await db["registrations"].find_one({"contest_id": contestId}, sort=[("rank", -1)])
    if last_registration:
        last_rank = last_registration["rank"]
    else:
        last_rank = 0  
    latest_rank = last_rank + 1
    
    # check if already registered for the contest   
    existing_registration = await db["registrations"].find_one({"contest_id": contestId, "emailaddress": email_address})
    if existing_registration:
        return {"status": "You have already participitated for this contest."}
    # create new registration record
    # deduct coins from user
    new_coins = user_coins - coins_required
    _ = await db["users"].update_one({"emailaddress": email_address}, {"$set": {"coins": new_coins}})
    
    # unique random number for prize_id
    unique_no = UniqueRandomGenerator(10, 999999).get_number()
    print(f"Generated unique number for prize_id: {unique_no}")
    prize_id = "PRIZE-" + str(unique_no)
    registration_data = {
        "emailaddress": email_address,
        "contest_id": offer["contest_id"],
        "offer_id": offer["offer_id"],
        "offer_name": offer["offer_name"],
        "shop_id": offer["shop_id"],
        "registration_date": datetime.utcnow(),
        "status": "PARTICIPATED",
        "rank": latest_rank,
        "claim_status": "UNCLAIMED",
        "prize_id": prize_id
    }
    _ = await db["registrations"].insert_one(registration_data)
    
    if latest_rank in offer.get("won_ranks", []):
        # update registration status to WON
        _ = await db["registrations"].update_one({"contest_id": contestId, "emailaddress": email_address}, {"$set": {"status": "WON"}})
        return {
            "status": registration_data["status"],
            "prizeStatus": "won",
            "prizeId": registration_data["prize_id"],
            "prizeName": offer.get("offer_name"),
            "currentStatus": registration_data["claim_status"],
            "prizeDescription": offer.get("description"),
            "validity": offer.get("validity_end_date"),
            "remainingCoins": new_coins
            }

    else:
        return {
                "status": registration_data["status"],
                "prizeStatus": "fail",
                "prizeId": None,
                "prizeName": None,
                "currentStatus": None,
                "prizeDescription": None,
                "validity": None,
                "remainingCoins": new_coins
                }
        
#get prize history
@router.get("/prizes/")
async def get_prize_history(email_address: str):
    registrations = [registration async for registration in db["registrations"].find({"emailaddress": email_address, "status": "WON"}, {"_id": 0})]
    return {"prizes": registrations} 

# get prize details by prize_id
@router.get("/prizes/{prize_id}")
async def get_prize_details(prize_id: str):
    prize = await db["registrations"].find_one({"prize_id": prize_id}, {"_id": 0})
    if not prize:
        raise HTTPException(status_code=404, detail="Prize not found")
    offer_id = prize.get("offer_id")
    # fetch offer details for the prize
    offer = await db["offers"].find_one({"offer_id": offer_id}, {"_id": 0})
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    return {
            "status": "success",
            "prizeStatus": prize.get("status"),
            "prizeId": prize.get("prize_id"),
            "prizeName": offer.get("offer_name") if offer else None,
            "currentStatus": prize.get("claim_status"),
            "prizeDescription": offer.get("description") if offer else None,
            "validity": offer.get("validity_end_date") if offer else None,
            }
