import os

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise RuntimeError("MONGO_URI is not set in the environment variables.")

client = AsyncIOMotorClient(MONGO_URI)

db: AsyncIOMotorDatabase = client["fairshare"]


async def connect_to_database() -> None:
    """
    Verify MongoDB connection.
    """
    await client.admin.command("ping")


async def close_database_connection() -> None:
    """
    Close MongoDB connection.
    """
    client.close()