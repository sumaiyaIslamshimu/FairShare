import os
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
db = client["fairshare"]
SAMPLE_PRODUCTS = [
    {
        "id": 1,
        "name": "Sony WH-1000XM5",
        "brand": "Sony",
        "category": "Headphones",
        "price": 299,
        "rating": 4.8,
        "marketplace": "AudioWorld",
    },
    {
        "id": 2,
        "name": "Apple AirPods Pro 2nd Gen",
        "brand": "Apple",
        "category": "Earbuds",
        "price": 189,
        "rating": 4.9,
        "marketplace": "TechVision Store",
    },
    {
        "id": 3,
        "name": "Samsung 65 QLED 4K TV",
        "brand": "Samsung",
        "category": "TV",
        "price": 1199,
        "rating": 4.7,
        "marketplace": "ElectroBuy",
    },
    {
        "id": 4,
        "name": "Bose QC Ultra Earbuds",
        "brand": "Bose",
        "category": "Earbuds",
        "price": 249,
        "rating": 4.7,
        "marketplace": "AudioWorld",
    },
]

@app.get("/health")
async def health_check():
    try:
        await client.admin.command("ping")
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/")
async def root():
    return {"message": "FairShare API is running"}

@app.get("/seller/profile")
async def get_seller_profile():
    profile = await db.sellers.find_one({}, {"_id": 0})

    if profile is None:
        profile = {
            "businessName": "TechVision Store",
            "description": "Premium electronics and gadgets.",
            "contactNumber": "15551234567",
            "address": "123 Market Street, Dhaka",
        }
        await db.sellers.insert_one(profile.copy())

    return profile


from pydantic import BaseModel, EmailStr
class BusinessProfile(BaseModel):
    businessName: str
    ownerName: str
    email: EmailStr
    contactNumber: str
    businessCategory: str
    website: Optional[str] = ""
    description: str


@app.get("/seller/profile")
async def get_seller_profile():
    profile = await db.sellers.find_one({}, {"_id": 0})

    if profile is None:
        profile = {
            "businessName": "TechVision Store",
            "ownerName": "Marcus Chen",
            "email": "marcus@techvision.com",
            "contactNumber": "15551234567",
            "businessCategory": "Electronics & Gadgets",
            "website": "https://techvision.store",
            "description": (
                "TechVision Store is your go-to destination for premium "
                "electronics and gadgets."
            ),
        }

        await db.sellers.insert_one(profile.copy())

    return profile


@app.put("/seller/profile")
async def update_seller_profile(data: BusinessProfile):
    await db.sellers.update_one(
        {},
        {"$set": data.model_dump()},
        upsert=True
    )

    updated_profile = await db.sellers.find_one({}, {"_id": 0})
    return updated_profile

VALID_SORTS = {"price_asc", "price_desc", "rating"}


@app.get("/products/search")
def search_products(
    q: Optional[str] = Query(None),
    minPrice: Optional[float] = Query(None),
    maxPrice: Optional[float] = Query(None),
    category: Optional[str] = Query(None),
    marketplace: Optional[str] = Query(None),
    sort: Optional[str] = Query(None),
):
    if not q or not q.strip():
        raise HTTPException(
            status_code=400,
            detail="Query parameter 'q' is required."
        )

    if sort is not None and sort not in VALID_SORTS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort value. Must be one of {sorted(VALID_SORTS)}."
        )

    keyword = q.lower()

    results = [
        product
        for product in SAMPLE_PRODUCTS
        if keyword in product["name"].lower()
        or keyword in product["brand"].lower()
        or keyword in product["category"].lower()
    ]

    # Price filters
    if minPrice is not None:
        results = [
            product for product in results
            if product["price"] >= minPrice
        ]

    if maxPrice is not None:
        results = [
            product for product in results
            if product["price"] <= maxPrice
        ]

    # Category filter
    if category is not None:
        results = [
            product for product in results
            if product["category"].lower() == category.lower()
        ]

    # Marketplace filter
    if marketplace is not None:
        results = [
            product for product in results
            if product["marketplace"].lower() == marketplace.lower()
        ]

    # Sorting
    if sort == "price_asc":
        results.sort(key=lambda product: product["price"])

    elif sort == "price_desc":
        results.sort(
            key=lambda product: product["price"],
            reverse=True
        )

    elif sort == "rating":
        results.sort(
            key=lambda product: product["rating"],
            reverse=True
        )

    return results