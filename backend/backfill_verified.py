import asyncio
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=True)

async def run():
    client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
    db = client["fairshare"]

    result = await db.sellers.update_many(
        {"is_verified": {"$exists": False}},
        {"$set": {"is_verified": False}},
    )

    print(f"Updated {result.modified_count} sellers")
    client.close()

if __name__ == "__main__":
    asyncio.run(run())