# models.py
from datetime import date, datetime
from pathlib import Path
from sqlalchemy import Column, String, Date, ForeignKey, Text, Boolean, Enum, DateTime, Integer # Added Integer
from sqlalchemy.orm import relationship
# Import UserMixin from Flask-Login
from flask_login import UserMixin
# Import password hashing utilities
from werkzeug.security import generate_password_hash, check_password_hash

# Import Base from db.py AFTER UserMixin to avoid potential circular imports if db imports models
from db import Base, ENG # Make sure Base is defined in db.py

# --- User Model ---
# Inherit from Base (for SQLAlchemy) and UserMixin (for Flask-Login)
class User(Base, UserMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True) # Simple integer ID is fine
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False) # Added email
    password_hash = Column(String(128)) # Store hash, not plain password
    role = Column(String(80), nullable=False, default='sspa') # e.g., 'admin', 'sspa'

    # Relationships (optional but can be useful)
    # completed_tasks = relationship("Progress", back_populates="user")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

    # Flask-Login expects a get_id method, which UserMixin provides using the primary key 'id'

# --- League Model ---
class League(Base):
    __tablename__ = "leagues"
    id   = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    season_start = Column(Date)
    season_end   = Column(Date)
    kind        = Column(Enum("league","tournament", name="league_kind"))
    officiated  = Column(Boolean, default=True)
    template_id = Column(String, ForeignKey("checklist_templates.id"))

    tasks = relationship("Task", back_populates="league",
                         cascade="all, delete-orphan",
                         order_by="Task.order")

# --- Task Model ---
class Task(Base):
    __tablename__ = "tasks"
    id        = Column(String, primary_key=True)
    league_id = Column(String, ForeignKey("leagues.id"), nullable=False)
    title     = Column(String, nullable=False)
    category  = Column(String, nullable=False)
    due       = Column(Date,   nullable=True)
    order     = Column(String, nullable=True)
    instructions = Column(Text, nullable=True)

    # --- Added Task Fields (Keep all from previous version) ---
    link_1_url = Column(String, nullable=True, comment="Generic Link 1 URL")
    link_1_label = Column(String, nullable=True, comment="Generic Link 1 Label (optional)")
    link_2_url = Column(String, nullable=True, comment="Generic Link 2 URL")
    link_2_label = Column(String, nullable=True, comment="Generic Link 2 Label (optional)")
    notes = Column(Text, nullable=True, comment="General notes area for the task")
    contact_info = Column(String, nullable=True, comment="Relevant contact person/email/phone")
    email_template_subject = Column(String, nullable=True, comment="Subject line for mailto link")
    email_template_body = Column(Text, nullable=True, comment="Body for mailto link")
    email_recipient_source = Column(String, nullable=True, comment="Hint for where to find recipients (e.g., Handshake link, file path)")
    email_target_address = Column(String, nullable=True, comment="Specific target email address for mailto (e.g., Macer/Tony)")
    previous_report_link = Column(String, nullable=True, comment="Task 1: Link to previous report")
    improvement_goals = Column(Text, nullable=True, comment="Task 1/4: Goals identified/set")
    imleagues_staff_link = Column(String, nullable=True, comment="Task 3: Link to IMLeagues staff page")
    offer_letter_template = Column(Text, nullable=True, comment="Task 3: Template text for offer letters")
    report_template_link = Column(String, nullable=True, comment="Task 4: Link to blank report template")
    pac_instructor_contact = Column(String, nullable=True, comment="Task 5: PAC Instructor Contact Info")
    pac_scheduled_datetime = Column(DateTime, nullable=True, comment="Task 5: Scheduled date/time for PAC presentation")
    facilities_contact = Column(String, nullable=True, comment="Task 6: Facilities Contact Info")
    facilities_booking_link = Column(String, nullable=True, comment="Task 6/7: Link to booking system (Mazevo?)")
    facilities_email_templates = Column(Text, nullable=True, comment="Task 6: Email templates for facility requests")
    imleagues_schedule_link = Column(String, nullable=True, comment="Task 7: Link to IMLeagues schedule page")
    clinic_booking_link = Column(String, nullable=True, comment="Task 8: Link to clinic room booking")
    clinic_datetime = Column(DateTime, nullable=True, comment="Task 8: Scheduled date/time for clinic")
    zoom_meeting_link = Column(String, nullable=True, comment="Task 9: Generated Zoom meeting link")
    imleagues_paste_location_link = Column(String, nullable=True, comment="Task 9: Link to where Zoom link should be pasted in IMLeagues")
    inventory_list_link = Column(String, nullable=True, comment="Task 10: Link to equipment inventory list")
    equipment_notes = Column(Text, nullable=True, comment="Task 10/20: Notes on equipment status/needs")
    rules_doc_link = Column(String, nullable=True, comment="Task 11: Link to rules document")
    imleagues_rules_upload_link = Column(String, nullable=True, comment="Task 11: Link to IMLeagues rules upload page")
    presentation_slides_link = Column(String, nullable=True, comment="Task 12: Link to presentation slides")
    interest_list_link = Column(String, nullable=True, comment="Task 12: Link to interest list form/sheet")
    whentowork_link = Column(String, nullable=True, comment="Task 13/18: Link to WhenToWork")
    imleagues_messaging_link = Column(String, nullable=True, comment="Task 14: Link to IMLeagues messaging tool")
    participant_message_templates = Column(Text, nullable=True, comment="Task 14: Templates for messaging participants")
    slides_template_link = Column(String, nullable=True, comment="Task 15: Link to slide deck template")
    captain_quiz_link = Column(String, nullable=True, comment="Task 15: Link to captain quiz")
    imleagues_email_link = Column(String, nullable=True, comment="Task 16: Link to IMLeagues email tool")
    spa_meeting_docs_link = Column(String, nullable=True, comment="Task 18: Link to docs for SPA meeting")
    spa_meeting_datetime = Column(DateTime, nullable=True, comment="Task 18: Scheduled date/time for SPA meeting")
    shirt_tracker_link = Column(String, nullable=True, comment="Task 19/23: Link to shirt tracker doc/sheet")
    flickr_link = Column(String, nullable=True, comment="Task 19/21: Link to Flickr album/upload")
    marketing_folder_link = Column(String, nullable=True, comment="Task 22: Link to marketing folder (S:/... or cloud)")
    jersey_checkin_link = Column(String, nullable=True, comment="Task 24: Link to jersey check-in list/form")
    summary_report_template_link = Column(String, nullable=True, comment="Task 25: Link to summary report template")
    summary_report_draft = Column(Text, nullable=True, comment="Task 25: Area to store generated draft snippets")
    # --- End Added Task Fields ---

    league = relationship("League", back_populates="tasks")
    # Relationship to Progress (one task can have multiple progress entries if needed, though likely 1 per user)
    progress_entries = relationship("Progress", back_populates="task", cascade="all, delete-orphan")


# --- Checklist Template Models ---
class ChecklistTemplate(Base):
    __tablename__ = "checklist_templates"
    id   = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    tasks = relationship("TemplateTask", back_populates="template",
                         cascade="all, delete-orphan",
                         order_by="TemplateTask.order")

class TemplateTask(Base):
    __tablename__ = "template_tasks"
    id          = Column(String, primary_key=True)
    template_id = Column(String, ForeignKey("checklist_templates.id"), nullable=False)
    task_ref_id  = Column(String, nullable=False)
    title        = Column(String, nullable=False)
    category     = Column(String, nullable=False)
    relative_due = Column(String, nullable=True)
    instructions = Column(Text, nullable=True)
    order        = Column(String, nullable=True)

    template = relationship("ChecklistTemplate", back_populates="tasks")

    # --- Mirrored Fields from Task (Keep all from previous version) ---
    link_1_url = Column(String, nullable=True)
    link_1_label = Column(String, nullable=True)
    link_2_url = Column(String, nullable=True)
    link_2_label = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    contact_info = Column(String, nullable=True)
    email_template_subject = Column(String, nullable=True)
    email_template_body = Column(Text, nullable=True)
    email_recipient_source = Column(String, nullable=True)
    email_target_address = Column(String, nullable=True)
    previous_report_link = Column(String, nullable=True)
    improvement_goals = Column(Text, nullable=True)
    imleagues_staff_link = Column(String, nullable=True)
    offer_letter_template = Column(Text, nullable=True)
    report_template_link = Column(String, nullable=True)
    pac_instructor_contact = Column(String, nullable=True)
    facilities_contact = Column(String, nullable=True)
    facilities_booking_link = Column(String, nullable=True)
    facilities_email_templates = Column(Text, nullable=True)
    imleagues_schedule_link = Column(String, nullable=True)
    clinic_booking_link = Column(String, nullable=True)
    zoom_meeting_link = Column(String, nullable=True)
    imleagues_paste_location_link = Column(String, nullable=True)
    inventory_list_link = Column(String, nullable=True)
    equipment_notes = Column(Text, nullable=True)
    rules_doc_link = Column(String, nullable=True)
    imleagues_rules_upload_link = Column(String, nullable=True)
    presentation_slides_link = Column(String, nullable=True)
    interest_list_link = Column(String, nullable=True)
    whentowork_link = Column(String, nullable=True)
    imleagues_messaging_link = Column(String, nullable=True)
    participant_message_templates = Column(Text, nullable=True)
    slides_template_link = Column(String, nullable=True)
    captain_quiz_link = Column(String, nullable=True)
    imleagues_email_link = Column(String, nullable=True)
    spa_meeting_docs_link = Column(String, nullable=True)
    shirt_tracker_link = Column(String, nullable=True)
    flickr_link = Column(String, nullable=True)
    marketing_folder_link = Column(String, nullable=True)
    jersey_checkin_link = Column(String, nullable=True)
    summary_report_template_link = Column(String, nullable=True)
    summary_report_draft = Column(Text, nullable=True)
    # --- End Mirrored Fields ---


# --- Progress Model Update ---
class Progress(Base):
    __tablename__ = "progress"
    # Composite primary key: one entry per user per task
    league_id = Column(String, ForeignKey('leagues.id'), primary_key=True) # Keep league_id part of PK
    task_id   = Column(String, ForeignKey('tasks.id'), primary_key=True)
    user_id   = Column(Integer, ForeignKey('users.id'), primary_key=True) # Add user_id as part of PK
    done_at   = Column(DateTime, default=datetime.utcnow)

    # Relationships (optional but useful)
    # user = relationship("User", back_populates="completed_tasks")
    task = relationship("Task", back_populates="progress_entries")

    def __repr__(self) -> str:
        return f"<Progress league={self.league_id} task={self.task_id} user={self.user_id}>"


# --- Create Tables ---
# Ensure this runs after all models are defined.
# Consider using Flask-Migrate or Alembic for production database management.
try:
    print("Checking/creating database tables...")
    Base.metadata.create_all(ENG)
    print("Database tables checked/created successfully.")
except Exception as e:
    print(f"Error creating database tables: {e}")

