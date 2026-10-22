from datetime import timezone
from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator):
    """Keep API timestamps in UTC regardless of the PostgreSQL session timezone."""
    impl = DateTime
    cache_ok = True

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        # SQLite stores the original UTC value without timezone metadata.
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
