from datetime import date
from pathlib import Path
from sqlalchemy import Column, String, Date, ForeignKey, Text
from sqlalchemy.orm import relationship

from db import Base, ENG

class League(Base):
    __tablename__ = "leagues"
    id   = Column(String, primary_key=True)  # e.g. "soccer"
    name = Column(String, nullable=False)

    tasks = relationship("Task", back_populates="league",
                         cascade="all, delete-orphan",
                         order_by="Task.order")

class Task(Base):
    __tablename__ = "tasks"
    id        = Column(String, primary_key=True)  # "review_reports"
    league_id = Column(String, ForeignKey("leagues.id"), nullable=False)
    title     = Column(String, nullable=False)
    category  = Column(String, nullable=False)          # Pre-League / Post-League
    due       = Column(Date,   nullable=True)
    order     = Column(String, nullable=True)           # for custom sorting
    instructions = Column(Text, nullable=True)

    league = relationship("League", back_populates="tasks")

# create tables if missing
Base.metadata.create_all(ENG)