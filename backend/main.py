from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from config.database import (
    close_database_connection,
    connect_to_database,
    db,
)

from routes.auth import router as auth_router
from routes.seller import router as seller_router
from routes.alerts import router as alerts_router
from routes.views import router as views_router
from routes.recommendations import router as recommendations_router
from routes.rentals import router as rentals_router
from routes.rental_requests import router as rental_requests_router

from app.routers import products
from routes.admin import router as admin_router

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

app.mongodb = db

app.include_router(products.router)

app.include_router(auth_router)
app.include_router(seller_router)
app.include_router(admin_router)
app.include_router(rentals_router)
app.include_router(alerts_router)
app.include_router(views_router)
app.include_router(recommendations_router)
app.include_router(rentals_router)
app.include_router(rental_requests_router)



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