from datetime import date
from pathlib import Path
from sqlalchemy import Column, String, Date, ForeignKey, Text, Boolean, Enum
from sqlalchemy.orm import relationship

from db import Base, ENG

class League(Base):
    __tablename__ = "leagues"
    id   = Column(String, primary_key=True)  # e.g. "soccer"
    name = Column(String, nullable=False)
    season_start = Column(Date)
    season_end   = Column(Date)

    tasks = relationship("Task", back_populates="league",
                         cascade="all, delete-orphan",
                         order_by="Task.order")

    kind        = Column(Enum("league","tournament", name="league_kind"))
    officiated  = Column(Boolean, default=True)
    template_id = Column(String, ForeignKey("checklist_templates.id"))

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

class ChecklistTemplate(Base):
    __tablename__ = "checklist_templates"
    id   = Column(String, primary_key=True)          # e.g. "officiated_league"
    name = Column(String, nullable=False)            # human label
    tasks = relationship("TemplateTask", back_populates="template",
                         cascade="all, delete-orphan",
                         order_by="TemplateTask.order")

class TemplateTask(Base):
    __tablename__ = "template_tasks"
    id          = Column(String, primary_key=True)   # e.g. "review_reports"
    template_id = Column(String, ForeignKey("checklist_templates.id"),
                          nullable=False)
    title        = Column(String, nullable=False)
    category     = Column(String, nullable=False)    # Pre-League / Post-League
    relative_due = Column(String, nullable=True)     # free-text (“4 weeks …”)
    instructions = Column(Text, nullable=True)
    order        = Column(String, nullable=True)

    template = relationship("ChecklistTemplate", back_populates="tasks")

# create tables if missing
Base.metadata.create_all(ENG)