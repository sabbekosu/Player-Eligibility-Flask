from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, Column, String, DateTime, Integer # Added Integer
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import ForeignKey # Added ForeignKey

# Define Base here
Base = declarative_base()

DB_PATH = Path(__file__).with_name("progress.db")
# echo=True can be useful for debugging SQL
ENG = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
SessionLocal = sessionmaker(bind=ENG, expire_on_commit=False)