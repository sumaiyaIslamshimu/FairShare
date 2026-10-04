import asyncio
from datetime import datetime, timedelta, timezone

from config.database import db


PRICE_HISTORY_COLLECTION = "price_history"
PRODUCTS_COLLECTION = "products"


async def seed_price_history() -> None:
    """
    Add sample price history for existing products.
    """

    products = await db[PRODUCTS_COLLECTION].find({}).to_list(
        length=None
    )

    if not products:
        print("No products found in the database.")
        return

    inserted_count = 0

    for product in products:
        product_id = str(product["_id"])

        base_price = product.get("price")

        if base_price is None:
            print(
                f"Skipping product {product_id}: "
                "price field not found."
            )
            continue

        try:
            base_price = float(base_price)
        except (TypeError, ValueError):
            print(
                f"Skipping product {product_id}: "
                "invalid price."
            )
            continue

        existing_history = await db[
            PRICE_HISTORY_COLLECTION
        ].count_documents(
            {"product_id": product_id}
        )

        if existing_history > 0:
            print(
                f"Skipping product {product_id}: "
                "price history already exists."
            )
            continue

        history_entries = []

        price_changes = [
            0.00,
            -20.00,
            15.00,
            -10.00,
            -25.00,
        ]

        for index, change in enumerate(price_changes):
            recorded_at = (
                datetime.now(timezone.utc)
                - timedelta(days=4 - index)
            )

            price = max(
                0.01,
                base_price + change,
            )

            history_entries.append(
                {
                    "product_id": product_id,
                    "price": price,
                    "recorded_at": recorded_at,
                }
            )

        result = await db[
            PRICE_HISTORY_COLLECTION
        ].insert_many(history_entries)

        inserted_count += len(result.inserted_ids)

        print(
            f"Added {len(result.inserted_ids)} "
            f"price history entries for product "
            f"{product_id}."
        )

    print(
        f"\nPrice history seeding completed. "
        f"Inserted entries: {inserted_count}"
    )


if __name__ == "__main__":
    asyncio.run(seed_price_history())