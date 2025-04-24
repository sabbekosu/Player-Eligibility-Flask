from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()
DB_PATH = Path(__file__).with_name("progress.db")
ENG = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
SessionLocal = sessionmaker(bind=ENG, expire_on_commit=False)


class Progress(Base):
    __tablename__ = "progress"
    league_id = Column(String, primary_key=True)
    task_id   = Column(String, primary_key=True)
    done_at   = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:  # debug nicety
        return f"<Progress {self.league_id}/{self.task_id}>"

# create tables at import time (OK for dev)
Base.metadata.create_all(ENG)