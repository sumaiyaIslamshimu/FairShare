from passlib.context import CryptContext

# CryptContext manages hashing scheme(s) and lets us upgrade algorithms
# later without changing calling code.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    Hash a plain-text password for storage.
    Never store plain_password directly in the database.
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compare a plain-text password (submitted at login) against
    the stored bcrypt hash. Returns True/False.
    """
    return pwd_context.verify(plain_password, hashed_password)