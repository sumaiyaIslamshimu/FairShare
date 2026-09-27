from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.database import (
    close_database_connection,
    connect_to_database,
)
from routes.auth import router as auth_router
from routes.seller import router as seller_router

# This tells Python to read your new router
from app.routers import products

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
app.mongodb = client["fairshare"]

# This attaches the /products/search URL to your API
app.include_router(products.router)

app.include_router(auth_router)
app.include_router(seller_router)


@app.on_event("startup")
async def startup():
    await connect_to_database()


@app.on_event("shutdown")
async def shutdown():
    await close_database_connection()


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "database": "connected",
    }


@app.get("/")
async def root():
    return {
        "message": "FairShare API is running"
    }