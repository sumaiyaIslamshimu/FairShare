import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
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

from routers.auth_routes import router as auth_router

app.include_router(auth_router)


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