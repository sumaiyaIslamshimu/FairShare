
from getpass import getpass

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.mongo import get_db

settings = get_settings()
db = get_db()

email = settings.admin_email.strip().lower()
admin = db.users.find_one({"email": email})

if not admin:
    print("Admin account not found.")
elif admin.get("role") != "admin":
    print("The account is not an admin. No changes made.")
else:
    new_password = getpass("Enter a NEW admin password: ")
    confirm_password = getpass("Confirm the new password: ")

    if len(new_password) < 12:
        print("Password must be at least 12 characters. No changes made.")
    elif new_password != confirm_password:
        print("Passwords do not match. No changes made.")
    else:
        result = db.users.update_one(
            {"_id": admin["_id"], "role": "admin"},
            {
                "$set": {
                    "password_hash": hash_password(new_password)
                }
            },
        )

        if result.modified_count == 1:
            print("Admin password updated successfully.")
        else:
            print("Password was not changed. Please check the account.")
