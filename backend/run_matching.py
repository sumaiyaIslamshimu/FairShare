import asyncio
import uuid
from config.database import connect_to_database, close_database_connection, db
from services.matching import generate_normalized_key, are_products_matching


async def group_matching_products():
    print("Connecting to database...")
    await connect_to_database()

    print("Fetching all products...")
    cursor = db.products.find({})
    products = await cursor.to_list(length=None)

    if not products:
        print("No products found to group.")
        await close_database_connection()
        return

    # 1. Generate normalized keys for everything
    for p in products:
        p["normalized_key"] = generate_normalized_key(
            name=p.get("name", ""),
            brand=p.get("brand", "")
        )

    # 2. Group the products
    groups = []  # A list of lists, where each inner list is a matching product group

    for p in products:
        matched = False
        for group in groups:
            # Compare against the first product in the existing group
            if are_products_matching(p, group[0]):
                group.append(p)
                p["group_id"] = group[0]["group_id"]
                matched = True
                break

        if not matched:
            # Create a brand new group ID using a unique string
            p["group_id"] = uuid.uuid4().hex
            groups.append([p])

    # 3. Save updates back to MongoDB
    print(f"Found {len(groups)} unique product groups. Updating database...")
    for p in products:
        await db.products.update_one(
            {"_id": p["_id"]},
            {"$set": {
                "normalized_key": p["normalized_key"],
                "group_id": p["group_id"]
            }}
        )

    print("Database updated successfully!")
    await close_database_connection()


if __name__ == "__main__":
    asyncio.run(group_matching_products())