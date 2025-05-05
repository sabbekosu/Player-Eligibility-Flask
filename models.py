# models.py
from datetime import date, datetime
from pathlib import Path
# Added Integer, Numeric, Boolean
from sqlalchemy import Column, String, Date, ForeignKey, Text, Boolean, Enum, DateTime, Integer, Numeric
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Import Base from db.py AFTER UserMixin
from db import Base, ENG

# --- User Model ---
class User(Base, UserMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128))
    role = Column(String(80), nullable=False, default='sspa') # 'admin', 'sspa'
    # Relationship back to progress entries made by this user
    # progress_entries = relationship("Progress", back_populates="user")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

# --- League/Task Models (Intramural Sports) ---
class League(Base):
    # ... (Existing League model definition - no changes needed here) ...
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

class Task(Base):
    # ... (Existing Task model definition with all fields - no changes needed here) ...
    __tablename__ = "tasks"
    id        = Column(String, primary_key=True)
    league_id = Column(String, ForeignKey("leagues.id"), nullable=False)
    title     = Column(String, nullable=False)
    category  = Column(String, nullable=False)
    due       = Column(Date,   nullable=True)
    order     = Column(String, nullable=True)
    instructions = Column(Text, nullable=True)
    # --- Added Task Fields ---
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
    progress_entries = relationship("Progress", back_populates="task", cascade="all, delete-orphan")

class ChecklistTemplate(Base):
    # ... (Existing ChecklistTemplate model definition - no changes needed here) ...
    __tablename__ = "checklist_templates"
    id   = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    tasks = relationship("TemplateTask", back_populates="template",
                         cascade="all, delete-orphan",
                         order_by="TemplateTask.order")

class TemplateTask(Base):
    # ... (Existing TemplateTask model definition with all fields - no changes needed here) ...
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
    # --- Mirrored Fields from Task ---
    link_1_url = Column(String, nullable=True); link_1_label = Column(String, nullable=True)
    link_2_url = Column(String, nullable=True); link_2_label = Column(String, nullable=True)
    notes = Column(Text, nullable=True); contact_info = Column(String, nullable=True)
    email_template_subject = Column(String, nullable=True); email_template_body = Column(Text, nullable=True)
    email_recipient_source = Column(String, nullable=True); email_target_address = Column(String, nullable=True)
    previous_report_link = Column(String, nullable=True); improvement_goals = Column(Text, nullable=True)
    imleagues_staff_link = Column(String, nullable=True); offer_letter_template = Column(Text, nullable=True)
    report_template_link = Column(String, nullable=True); pac_instructor_contact = Column(String, nullable=True)
    facilities_contact = Column(String, nullable=True); facilities_booking_link = Column(String, nullable=True)
    facilities_email_templates = Column(Text, nullable=True); imleagues_schedule_link = Column(String, nullable=True)
    clinic_booking_link = Column(String, nullable=True); zoom_meeting_link = Column(String, nullable=True)
    imleagues_paste_location_link = Column(String, nullable=True); inventory_list_link = Column(String, nullable=True)
    equipment_notes = Column(Text, nullable=True); rules_doc_link = Column(String, nullable=True)
    imleagues_rules_upload_link = Column(String, nullable=True); presentation_slides_link = Column(String, nullable=True)
    interest_list_link = Column(String, nullable=True); whentowork_link = Column(String, nullable=True)
    imleagues_messaging_link = Column(String, nullable=True); participant_message_templates = Column(Text, nullable=True)
    slides_template_link = Column(String, nullable=True); captain_quiz_link = Column(String, nullable=True)
    imleagues_email_link = Column(String, nullable=True); spa_meeting_docs_link = Column(String, nullable=True)
    shirt_tracker_link = Column(String, nullable=True); flickr_link = Column(String, nullable=True)
    marketing_folder_link = Column(String, nullable=True); jersey_checkin_link = Column(String, nullable=True)
    summary_report_template_link = Column(String, nullable=True); summary_report_draft = Column(Text, nullable=True)
    # --- End Mirrored Fields ---

class Progress(Base):
    # ... (Existing Progress model definition - no changes needed here) ...
    __tablename__ = "progress"
    league_id = Column(String, ForeignKey('leagues.id'), primary_key=True)
    task_id   = Column(String, ForeignKey('tasks.id'), primary_key=True)
    user_id   = Column(Integer, ForeignKey('users.id'), primary_key=True)
    done_at   = Column(DateTime, default=datetime.utcnow)
    task = relationship("Task", back_populates="progress_entries")
    # Add relationship to User if needed
    # user = relationship("User", back_populates="progress_entries")
    def __repr__(self): return f"<Progress league={self.league_id} task={self.task_id} user={self.user_id}>"


# --- NEW Sports Club Models ---
class Club(Base):
    """Represents an official Sports Club."""
    __tablename__ = "clubs"
    id = Column(Integer, primary_key=True)
    name = Column(String(150), unique=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationship to transactions allocated to this club
    foundation_transactions = relationship("FoundationTransaction", back_populates="club")

    def __repr__(self):
        return f"<Club {self.id}: {self.name}{'' if self.is_active else ' (Inactive)'}>"

class FoundationTransaction(Base):
    """Represents a reconciled transaction from the foundation reports."""
    __tablename__ = "foundation_transactions"
    id = Column(Integer, primary_key=True)
    transaction_date = Column(Date, nullable=False, index=True)
    journal_ref = Column(String(100), unique=True, nullable=False, index=True) # Unique identifier
    donor_description = Column(Text, nullable=True) # From DRS Report 'Description'
    original_designation = Column(Text, nullable=True) # From Donor Report 'Designation Desc'

    # Using Numeric for currency is recommended for precision
    gross_amount = Column(Numeric(10, 2), nullable=False, default=0.00) # Deduced income amount
    fees_total = Column(Numeric(10, 2), nullable=False, default=0.00) # Sum of all fees
    net_amount = Column(Numeric(10, 2), nullable=False, default=0.00) # gross_amount - fees_total

    # Link to the assigned club (can be null if unallocated/needs review initially)
    club_id = Column(Integer, ForeignKey('clubs.id'), nullable=True, index=True)
    club = relationship("Club", back_populates="foundation_transactions")
    # Store the name used at the time of reconciliation for easier export
    assigned_club_name = Column(String(150), nullable=True)

    # Status tracking
    STATUS_NEEDS_REVIEW = 'needs_review'
    STATUS_RECONCILED = 'reconciled'
    STATUS_IGNORED = 'ignored' # Maybe for transactions that shouldn't be included
    status = Column(String(50), nullable=False, default=STATUS_NEEDS_REVIEW, index=True)

    # Optional: Track which upload batch this came from
    # upload_batch_id = Column(String(100), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<FoundationTransaction {self.id} ({self.transaction_date}) JnlRef:{self.journal_ref} Net:{self.net_amount} Club:{self.assigned_club_name or self.club_id} Status:{self.status}>"

# --- Create Tables ---
try:
    print("Checking/creating database tables...")
    Base.metadata.create_all(ENG)
    print("Database tables checked/created successfully.")
except Exception as e:
    print(f"Error creating database tables: {e}")

