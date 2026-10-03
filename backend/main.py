from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from config.database import (
    close_database_connection,
    connect_to_database,
)

from routes.auth import router as auth_router
from routes.seller import router as seller_router
from routes.alerts import router as alerts_router
from routes.products import router as products_router


from app.routers import products


app = FastAPI(
    swagger_ui_persist_authorization=True
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


app.include_router(products.router)

app.include_router(auth_router)
app.include_router(seller_router)
app.include_router(alerts_router)


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