import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

base_products = [
    {"name": "Lotto BLACK SUPERLIGHT Shoes", "brand": "Lotto", "category": "Footwear", "price": 2100, "rating": 4.6, "marketplace_name": "Lotto", "in_stock": True},
    {"name": "Lotto BLACK SUPERLIGHT Shoes", "brand": "Lotto", "category": "Footwear", "price": 2150, "rating": 4.4, "marketplace_name": "Daraz", "in_stock": True},
    {"name": "Bata Formal Slip-on Sandals", "brand": "Bata", "category": "Footwear", "price": 1500, "rating": 4.2, "marketplace_name": "Bata", "in_stock": True},
    {"name": "Bata Formal Slip-on Sandals", "brand": "Bata", "category": "Footwear", "price": 1450, "rating": 4.1, "marketplace_name": "Daraz", "in_stock": False},

    # Rental products
    {"name": "ThinkPad L14 Gen 3", "brand": "Lenovo", "category": "Electronics", "price": 80000, "rating": 4.5, "marketplace_name": "Our Page", "in_stock": True},
    {"name": "Sony WH-1000XM4 Noise Cancelling", "brand": "Sony", "category": "Electronics", "price": 18000, "rating": 4.6, "marketplace_name": "Our Page", "in_stock": True},
    {"name": "Logitech MX Master 3S Mouse", "brand": "Logitech", "category": "Electronics", "price": 12000, "rating": 4.7, "marketplace_name": "Our Page", "in_stock": True},
    {"name": "Samsung Galaxy S23 Ultra", "brand": "Samsung", "category": "Electronics", "price": 100000, "rating": 4.6, "marketplace_name": "Our Page", "in_stock": True},
    {"name": "Walton Blender Machine", "brand": "Walton", "category": "Household", "price": 3500, "rating": 4.2, "marketplace_name": "Our Page", "in_stock": True},
    {"name": "Vision Microwave Oven 20L", "brand": "Vision", "category": "Household", "price": 9000, "rating": 4.3, "marketplace_name": "Our Page", "in_stock": True},
    {"name": "Philips Steam Iron", "brand": "Philips", "category": "Household", "price": 2500, "rating": 4.4, "marketplace_name": "Our Page", "in_stock": True},
    {"name": "FS Canvas Everyday Backpack", "brand": "FairShare", "category": "Accessories", "price": 1500, "rating": 4.1, "marketplace_name": "Our Page", "in_stock": True},
]

RENTAL_INFO = {
    "ThinkPad L14 Gen 3": (1200, "Dhaka"),
    "Sony WH-1000XM4 Noise Cancelling": (500, "Dhaka"),
    "Logitech MX Master 3S Mouse": (200, "Chattogram"),
    "Samsung Galaxy S23 Ultra": (2500, "Dhaka"),
    "Walton Blender Machine": (150, "Dhaka"),
    "Vision Microwave Oven 20L": (300, "Chattogram"),
    "Philips Steam Iron": (100, "Sylhet"),
    "FS Canvas Everyday Backpack": (80, "Dhaka"),
}

categories = ["Footwear", "Electronics", "Accessories"]
marketplaces = ["Bata", "Lotto", "Daraz"]

# Generate filler products to hit the 30-item minimum
for i in range(18):
    base_products.append({
        "name": f"Generic Product {i+1}",
        "brand": "GenericBrand",
        "category": categories[i % len(categories)],
        "price": 500 + (i * 100),
        "rating": 3.5 + (i % 15) * 0.1,
        "marketplace_name": marketplaces[i % len(marketplaces)],
        "in_stock": True
    })

# Add rental information to each product
for product in base_products:
    price_per_day, location = RENTAL_INFO.get(
        product["name"], (None, None)
    )
    product["is_rentable"] = price_per_day is not None
    product["price_per_day"] = price_per_day
    product["location"] = location

async def seed_db():
    client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
    db = client["fairshare"]
    await db.products.delete_many({})
    await db.products.insert_many(base_products)
    print("Database seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_db())