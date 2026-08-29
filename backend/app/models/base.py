from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

def get_utc_now():
    return datetime.now(timezone.utc)
