import os
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
db = client["fairshare"]

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