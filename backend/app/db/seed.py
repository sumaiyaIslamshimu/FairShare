"""Seed script: python -m app.db.seed   (run from the backend/ folder)."""
from datetime import datetime, timezone

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.indexes import ensure_indexes
from app.db.mongo import get_db
from app.db.taxonomy import TAXONOMY


def _now():
    return datetime.now(timezone.utc)


def seed_categories(db) -> None:
    for order, (slug, (name, subs)) in enumerate(TAXONOMY.items()):
        db.categories.update_one(
            {"slug": slug},
            {"$setOnInsert": {"slug": slug, "name": name, "is_active": True, "order": order}},
            upsert=True,
        )
        for sub_slug, sub_name in subs.items():
            # name/parent are kept in sync; is_active is only set on insert so an admin's choice is never overwritten.
            db.subcategories.update_one(
                {"slug": sub_slug},
                {"$set": {"category_slug": slug, "name": sub_name},
                 "$setOnInsert": {"slug": sub_slug, "is_active": True}},
                upsert=True,
            )
    keep = [s for _, (_, subs) in TAXONOMY.items() for s in subs]
    # Old slugs from the first taxonomy are hidden, not deleted.
    db.subcategories.update_many({"slug": {"$nin": keep}}, {"$set": {"is_active": False}})


def seed_admin(db, email: str, password: str) -> bool:
    """Creates the first admin if missing. Returns True if created."""
    email = email.lower().strip()
    if not email or not password or db.users.find_one({"email": email}):
        return False
    now = _now()
    db.users.insert_one({
        "email": email, "full_name": "Platform Admin", "phone": "", "password_hash": hash_password(password),
        "role": "admin", "is_active": True, "verification_status": "none",
        "created_at": now, "updated_at": now,
    })
    return True


def main() -> None:
    db = get_db()
    ensure_indexes(db)
    seed_categories(db)
    s = get_settings()
    created = seed_admin(db, s.admin_email, s.admin_password)
    print("Categories seeded.")
    print("Admin created." if created else "Admin not created (missing ADMIN_EMAIL/ADMIN_PASSWORD or already exists).")


if __name__ == "__main__":
    main()