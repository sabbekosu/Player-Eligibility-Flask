# bootstrap_db.py
from db import Base, ENG
import models  # noqa: ensures the new classes are registered

print("Creating any missing tables…")
Base.metadata.create_all(ENG)
print("✅ Done.")
