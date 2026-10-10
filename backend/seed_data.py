
import asyncio
import os

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient


load_dotenv()

DATABASE_NAME = "fairshare"
PRODUCTS_COLLECTION = "products"
USERS_COLLECTION = "users"


base_products = [
    {
        "name": "Lotto BLACK SUPERLIGHT Shoes",
        "brand": "Lotto",
        "category": "Footwear",
        "price": 2100,
        "rating": 4.6,
        "marketplace_name": "Lotto",
        "in_stock": True,
    },
    {
        "name": "Lotto BLACK SUPERLIGHT Shoes",
        "brand": "Lotto",
        "category": "Footwear",
        "price": 2150,
        "rating": 4.4,
        "marketplace_name": "Daraz",
        "in_stock": True,
    },
    {
        "name": "Bata Formal Slip-on Sandals",
        "brand": "Bata",
        "category": "Footwear",
        "price": 1500,
        "rating": 4.2,
        "marketplace_name": "Bata",
        "in_stock": True,
    },
    {
        "name": "Bata Formal Slip-on Sandals",
        "brand": "Bata",
        "category": "Footwear",
        "price": 1450,
        "rating": 4.1,
        "marketplace_name": "Daraz",
        "in_stock": False,
    },
]

categories = ["Footwear", "Electronics", "Accessories"]
marketplaces = ["Bata", "Lotto", "Daraz"]


# Generate the remaining products to reach 30 seed products.
for i in range(26):
    base_products.append(
        {
            "name": f"Generic Product {i + 1}",
            "brand": "GenericBrand",
            "category": categories[i % len(categories)],
            "price": 500 + (i * 100),
            "rating": round(3.5 + (i % 15) * 0.1, 1),
            "marketplace_name": marketplaces[
                i % len(marketplaces)
            ],
            "in_stock": True,
        }
    )


def prepare_product(product: dict, seller_id: str) -> dict:
    """
    Add rental fields and a stable key to each seeded product.
    """

    prepared = product.copy()

    # Stable key prevents duplicate seed products on reruns.
    prepared["seed_key"] = (
        f"{prepared['name']}|{prepared['marketplace_name']}"
    )

    # Rental fields required by the rental API.
    prepared["is_rentable"] = True
    prepared["price_per_day"] = max(
        50,
        round(prepared["price"] * 0.05, 2),
    )

    # Use an actual seller from the users collection.
    # Keep these as strings to match the rental service.
    prepared["owner_id"] = seller_id
    prepared["seller_id"] = seller_id

    return prepared


async def seed_db():
    mongo_uri = os.getenv("MONGO_URI")

    if not mongo_uri:
        raise RuntimeError(
            "MONGO_URI is missing. Check the backend .env file."
        )

    client = AsyncIOMotorClient(mongo_uri)

    try:
        db = client[DATABASE_NAME]

        # Find a real seller account.
        seller = await db[USERS_COLLECTION].find_one(
            {"role": "seller"},
            {"_id": 1},
        )

        if not seller:
            raise RuntimeError(
                "No seller account found in the users collection. "
                "Create/register a seller account before running "
                "this seed script. No products were changed."
            )

        seller_id = str(seller["_id"])

        products_collection = db[PRODUCTS_COLLECTION]

        inserted_count = 0
        updated_count = 0

        for product in base_products:
            prepared = prepare_product(product, seller_id)

            result = await products_collection.update_one(
                {"seed_key": prepared["seed_key"]},
                {"$set": prepared},
                upsert=True,
            )

            if result.upserted_id is not None:
                inserted_count += 1
            elif result.modified_count > 0:
                updated_count += 1

        print("Seed data processed successfully.")
        print(f"Seller ID assigned: {seller_id}")
        print(f"Seed products processed: {len(base_products)}")
        print(f"New products inserted: {inserted_count}")
        print(f"Existing seed products updated: {updated_count}")
        print("Existing non-seed products were not deleted.")

    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(seed_db())
