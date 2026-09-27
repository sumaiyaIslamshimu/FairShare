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
]

categories = ["Footwear", "Electronics", "Accessories"]
marketplaces = ["Bata", "Lotto", "Daraz"]

# Generate filler products to hit the 30-item minimum
for i in range(26):
    base_products.append({
        "name": f"Generic Product {i+1}",
        "brand": "GenericBrand",
        "category": categories[i % len(categories)],
        "price": 500 + (i * 100),
        "rating": 3.5 + (i % 15) * 0.1,
        "marketplace_name": marketplaces[i % len(marketplaces)],
        "in_stock": True
    })

async def seed_db():
    client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
    db = client["fairshare"]
    await db.products.delete_many({})
    await db.products.insert_many(base_products)
    print("Database seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_db())