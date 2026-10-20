"""Small time helpers. MongoDB returns naive UTC datetimes, so everything is made timezone-aware here."""
from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def aware(dt):
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def iso(dt):
    """ISO string with an explicit UTC offset, so the browser never reads it as local time."""
    a = aware(dt)
    return a.isoformat() if a else None