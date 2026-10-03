import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

base_products = [
    # --- EXTERNAL SELLERS (is_verified: False) ---
    {"name": "Lotto BLACK SUPERLIGHT Shoes (Size 44)", "brand": "Lotto", "category": "Fashion", "price": 2100,
     "rating": 4.6, "marketplace_name": "Lotto.com.bd", "in_stock": True, "is_verified": False},
    {"name": "Bata Formal Slip-on Sandals", "brand": "Bata", "category": "Fashion", "price": 1450, "rating": 4.1,
     "marketplace_name": "Bata.com.bd", "in_stock": True, "is_verified": False},
    {"name": "Men's Premium Cotton Polo", "brand": "Apex", "category": "Fashion", "price": 850, "rating": 4.3,
     "marketplace_name": "Apex4u.com", "in_stock": True, "is_verified": False},
    {"name": "Denim Regular Fit Jeans", "brand": "Lees", "category": "Fashion", "price": 1200, "rating": 4.0,
     "marketplace_name": "Daraz.com.bd", "in_stock": True, "is_verified": False},
    {"name": "Classic Genuine Leather Wallet", "brand": "SS Leather", "category": "Fashion", "price": 650,
     "rating": 4.5, "marketplace_name": "Daraz.com.bd", "in_stock": False, "is_verified": False},

    {"name": "ThinkPad L14 Gen 3", "brand": "Lenovo", "category": "Electronics", "price": 85000, "rating": 4.8,
     "marketplace_name": "Startech.com.bd", "in_stock": True, "is_verified": False},
    {"name": "Sony WH-1000XM4 Noise Cancelling", "brand": "Sony", "category": "Electronics", "price": 32000,
     "rating": 4.9, "marketplace_name": "Pickaboo.com", "in_stock": True, "is_verified": False},
    {"name": "Logitech MX Master 3S Mouse", "brand": "Logitech", "category": "Electronics", "price": 10500,
     "rating": 4.7, "marketplace_name": "Startech.com.bd", "in_stock": True, "is_verified": False},
    {"name": "Samsung Galaxy S23 Ultra", "brand": "Samsung", "category": "Electronics", "price": 135000, "rating": 4.8,
     "marketplace_name": "Pickaboo.com", "in_stock": False, "is_verified": False},
    {"name": "Apple AirPods Pro (2nd Gen)", "brand": "Apple", "category": "Electronics", "price": 26500, "rating": 4.6,
     "marketplace_name": "Gadgetandgear.com", "in_stock": True, "is_verified": False},

    {"name": "Walton Blender Machine", "brand": "Walton", "category": "Household", "price": 3200, "rating": 4.4,
     "marketplace_name": "Waltonbd.com", "in_stock": True, "is_verified": False},
    {"name": "Vision Microwave Oven 20L", "brand": "Vision", "category": "Household", "price": 7500, "rating": 4.2,
     "marketplace_name": "Othoba.com", "in_stock": True, "is_verified": False},
    {"name": "Philips Steam Iron", "brand": "Philips", "category": "Household", "price": 2800, "rating": 4.5,
     "marketplace_name": "Daraz.com.bd", "in_stock": True, "is_verified": False},
    {"name": "RFL Plastic Wardrobe 5 Drawer", "brand": "RFL", "category": "Household", "price": 4800, "rating": 4.1,
     "marketplace_name": "Othoba.com", "in_stock": True, "is_verified": False},
    {"name": "Miyako Electric Kettle 1.5L", "brand": "Miyako", "category": "Household", "price": 1250, "rating": 4.3,
     "marketplace_name": "Daraz.com.bd", "in_stock": True, "is_verified": False},

    {"name": "Fresh Miniket Rice 5kg", "brand": "Fresh", "category": "Groceries", "price": 380, "rating": 4.7,
     "marketplace_name": "Chaldal.com", "in_stock": True, "is_verified": False},
    {"name": "Radhuni Pure Mustard Oil 1L", "brand": "Radhuni", "category": "Groceries", "price": 260, "rating": 4.8,
     "marketplace_name": "Chaldal.com", "in_stock": True, "is_verified": False},
    {"name": "Maggi 2-Minute Noodles 8 Pack", "brand": "Maggi", "category": "Groceries", "price": 160, "rating": 4.6,
     "marketplace_name": "Daraz.com.bd", "in_stock": True, "is_verified": False},
    {"name": "Aarong Dairy Pasteurized Milk 1L", "brand": "Aarong Dairy", "category": "Groceries", "price": 90,
     "rating": 4.9, "marketplace_name": "Chaldal.com", "in_stock": True, "is_verified": False},
    {"name": "Ispahani Mirzapore Tea Bag (50 pcs)", "brand": "Ispahani", "category": "Groceries", "price": 130,
     "rating": 4.8, "marketplace_name": "Chaldal.com", "in_stock": True, "is_verified": False},

    # --- DIRECT SELLERS (is_verified: True) ---
    {"name": "FS Premium Cotton T-Shirt", "brand": "FS Basics", "category": "Fashion", "price": 450, "rating": 4.9,
     "marketplace_name": "Urban Threads", "in_stock": True, "is_verified": True},
    {"name": "FS Canvas Everyday Backpack", "brand": "FS Basics", "category": "Fashion", "price": 1100, "rating": 4.8,
     "marketplace_name": "Urban Threads", "in_stock": True, "is_verified": True},

    {"name": "FS 20W Fast Charging Adapter", "brand": "FS Tech", "category": "Electronics", "price": 650, "rating": 4.7,
     "marketplace_name": "Gadget Hub", "in_stock": True, "is_verified": True},
    {"name": "FS Nylon Braided Type-C Cable", "brand": "FS Tech", "category": "Electronics", "price": 350,
     "rating": 4.8, "marketplace_name": "Gadget Hub", "in_stock": True, "is_verified": True},

    {"name": "FS Microfiber Cleaning Cloth (10 Pcs)", "brand": "FS Home", "category": "Household", "price": 400,
     "rating": 4.9, "marketplace_name": "Prime Home Goods", "in_stock": True, "is_verified": True},
    {"name": "FS Bamboo Cutting Board", "brand": "FS Home", "category": "Household", "price": 850, "rating": 4.7,
     "marketplace_name": "Prime Home Goods", "in_stock": True, "is_verified": True},

    {"name": "FS Organic Green Tea Leaves 200g", "brand": "FS Pantry", "category": "Groceries", "price": 280,
     "rating": 4.8, "marketplace_name": "Fresh Harvest Pantry", "in_stock": True, "is_verified": True},
    {"name": "FS Premium Mixed Nuts 250g", "brand": "FS Pantry", "category": "Groceries", "price": 550, "rating": 4.9,
     "marketplace_name": "Fresh Harvest Pantry", "in_stock": True, "is_verified": True}
]

async def seed_db():
    client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
    db = client["fairshare"]
    await db.products.delete_many({})
    await db.products.insert_many(base_products)
    print("Database seeded with generic verified seller names and boolean flags!")

if __name__ == "__main__":
    asyncio.run(seed_db())