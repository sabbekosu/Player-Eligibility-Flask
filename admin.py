# admin.py
from flask import Blueprint, render_template, redirect, url_for, request, abort, flash
from flask_login import login_required, current_user
from functools import wraps
from flask_wtf import FlaskForm
import re
# Added BooleanField
from wtforms import StringField, SelectField, DateField, TextAreaField, DateTimeField, BooleanField
# Added Length validator
from wtforms.validators import DataRequired, Optional, Length, ValidationError

from db import SessionLocal
# Import Club model along with others
from models import League as DbLeague, Task as DbTask, TemplateTask as DbTemplateTask, User, Club as DbClub
from sqlalchemy.orm import selectinload, joinedload
from datetime import date, timedelta, datetime
import sys # Keep sys import

# --- Role Checking Decorator (Keep existing) ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required for this page.', 'danger')
            abort(403) # Forbidden
        return f(*args, **kwargs)
    return decorated_function

# --- Local get_league if not importing (Keep existing) ---
def get_league(league_id: str) -> DbLeague | None:
    """Return League with tasks eagerly loaded (safe outside session)."""
    with SessionLocal() as db:
        return (
            db.query(DbLeague)
              .options(joinedload(DbLeague.tasks))
              .get(league_id)
        )
# -----------------------------------------

admin = Blueprint("admin", __name__, url_prefix="/admin",
                  template_folder="templates")

# --- Forms ---

class LeagueForm(FlaskForm):
    # ... (Keep existing LeagueForm code) ...
    id   = StringField("ID", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    season_start = DateField("Season start", format="%Y-%m-%d", validators=[Optional()])
    season_end   = DateField("Season end",   format="%Y-%m-%d", validators=[Optional()])
    kind = SelectField("Kind", choices=[("league","League"),("tournament","Tournament")])
    officiated = SelectField("Officials", choices=[("yes","Officiated"),("no","Non-officiated")])

class TaskForm(FlaskForm):
    # ... (Keep existing TaskForm code with all fields) ...
    # Core Task Fields
    id    = StringField("ID", validators=[DataRequired(message="Task ID is required.")])
    title = StringField("Title", validators=[DataRequired(message="Title is required.")])
    category = SelectField("Category",
                           choices=[("Pre-League","Pre-League"),
                                    ("Post-League","Post-League"),
                                    ("Pre-Event", "Pre-Event"),
                                    ("Post-Event", "Post-Event")],
                           validators=[DataRequired()])
    due   = DateField("Due Date (YYYY-MM-DD)", format="%Y-%m-%d", validators=[Optional()])
    order = StringField("Sort Order", validators=[Optional()])
    instructions = TextAreaField("Instructions", validators=[Optional()])
    # --- NEW FIELDS ---
    link_1_url = StringField("Link 1 URL", validators=[Optional()])
    link_1_label = StringField("Link 1 Label", validators=[Optional()])
    link_2_url = StringField("Link 2 URL", validators=[Optional()])
    link_2_label = StringField("Link 2 Label", validators=[Optional()])
    notes = TextAreaField("Notes", validators=[Optional()])
    contact_info = StringField("Contact Info", validators=[Optional()])
    email_template_subject = StringField("Email Template Subject", validators=[Optional()])
    email_template_body = TextAreaField("Email Template Body", validators=[Optional()])
    email_recipient_source = StringField("Email Recipient Source Hint", validators=[Optional()])
    email_target_address = StringField("Specific Email Target", validators=[Optional()])
    previous_report_link = StringField("Previous Report Link", validators=[Optional()])
    improvement_goals = TextAreaField("Improvement Goals", validators=[Optional()])
    imleagues_staff_link = StringField("IMLeagues Staff Link", validators=[Optional()])
    offer_letter_template = TextAreaField("Offer Letter Template", validators=[Optional()])
    report_template_link = StringField("Report Template Link", validators=[Optional()])
    pac_instructor_contact = StringField("PAC Instructor Contact", validators=[Optional()])
    pac_scheduled_datetime = DateTimeField("PAC Scheduled DateTime (YYYY-MM-DD HH:MM)", format="%Y-%m-%d %H:%M", validators=[Optional()])
    facilities_contact = StringField("Facilities Contact", validators=[Optional()])
    facilities_booking_link = StringField("Facilities Booking Link", validators=[Optional()])
    facilities_email_templates = TextAreaField("Facilities Email Templates", validators=[Optional()])
    imleagues_schedule_link = StringField("IMLeagues Schedule Link", validators=[Optional()])
    clinic_booking_link = StringField("Clinic Booking Link", validators=[Optional()])
    clinic_datetime = DateTimeField("Clinic DateTime (YYYY-MM-DD HH:MM)", format="%Y-%m-%d %H:%M", validators=[Optional()])
    zoom_meeting_link = StringField("Zoom Meeting Link", validators=[Optional()])
    imleagues_paste_location_link = StringField("IMLeagues Paste Location Link", validators=[Optional()])
    inventory_list_link = StringField("Inventory List Link", validators=[Optional()])
    equipment_notes = TextAreaField("Equipment Notes", validators=[Optional()])
    rules_doc_link = StringField("Rules Doc Link", validators=[Optional()])
    imleagues_rules_upload_link = StringField("IMLeagues Rules Upload Link", validators=[Optional()])
    presentation_slides_link = StringField("Presentation Slides Link", validators=[Optional()])
    interest_list_link = StringField("Interest List Link", validators=[Optional()])
    whentowork_link = StringField("WhenToWork Link", validators=[Optional()])
    imleagues_messaging_link = StringField("IMLeagues Messaging Link", validators=[Optional()])
    participant_message_templates = TextAreaField("Participant Message Templates", validators=[Optional()])
    slides_template_link = StringField("Slides Template Link", validators=[Optional()])
    captain_quiz_link = StringField("Captain Quiz Link", validators=[Optional()])
    imleagues_email_link = StringField("IMLeagues Email Link", validators=[Optional()])
    spa_meeting_docs_link = StringField("SPA Meeting Docs Link", validators=[Optional()])
    spa_meeting_datetime = DateTimeField("SPA Meeting DateTime (YYYY-MM-DD HH:MM)", format="%Y-%m-%d %H:%M", validators=[Optional()])
    shirt_tracker_link = StringField("Shirt Tracker Link", validators=[Optional()])
    flickr_link = StringField("Flickr Link", validators=[Optional()])
    marketing_folder_link = StringField("Marketing Folder Link", validators=[Optional()])
    jersey_checkin_link = StringField("Jersey Check-in Link", validators=[Optional()])
    summary_report_template_link = StringField("Summary Report Template Link", validators=[Optional()])
    summary_report_draft = TextAreaField("Summary Report Draft Snippets", validators=[Optional()])
    # --- End New Fields ---

# --- NEW Club Form ---
class ClubForm(FlaskForm):
    name = StringField('Club Name', validators=[DataRequired(), Length(max=150)])
    is_active = BooleanField('Is Active?', default=True)

    # Custom validator to check for duplicate names (case-insensitive) during creation/edit
    def validate_name(self, name):
        with SessionLocal() as db:
            # Get the club ID from the form object if available (for editing)
            club_id = getattr(self, '_obj', None) and getattr(self._obj, 'id', None)
            query = db.query(DbClub).filter(DbClub.name.ilike(name.data)) # Case-insensitive check
            if club_id:
                query = query.filter(DbClub.id != club_id) # Exclude self during edit
            existing_club = query.first()
            if existing_club:
                raise ValidationError(f"A club with the name '{name.data}' already exists.")

# --- resolve_due function (Keep existing) ---
def resolve_due(token, season_start, season_end, task_lookup=None):
    # ... (keep existing code) ...
    if not token: return None
    if task_lookup is None: task_lookup = {}
    try:
        m = re.match(r"W([-+])(\d+)(e?)$", token, re.I)
        if m:
            sign, num, to_end = m.groups(); num = int(num)
            base = season_end if to_end else season_start
            if not base: return None
            if isinstance(base, date) and not isinstance(base, datetime): base = datetime.combine(base, datetime.min.time())
            delta = timedelta(weeks=num); return base + delta if sign == "+" else base - delta
        m = re.match(r"D([-+])(\d+)(e?)$", token, re.I)
        if m:
            sign, num, to_end = m.groups(); num = int(num)
            base = season_end if to_end else season_start
            if not base: return None
            if isinstance(base, date) and not isinstance(base, datetime): base = datetime.combine(base, datetime.min.time())
            delta = timedelta(days=num); return base + delta if sign == "+" else base - delta
        m = re.match(r"D\+(\d+)t:([\w-]+)", token, re.I)
        if m:
            days, dep_ref_id = m.groups()
            base_date = task_lookup.get(dep_ref_id)
            if base_date and isinstance(base_date, (date, datetime)):
                if not isinstance(base_date, datetime): base_date = datetime.combine(base_date, datetime.min.time())
                return base_date + timedelta(days=int(days))
            else: return None
    except (ValueError, TypeError) as e: return None
    return None

# ── Routes ─────────────────────────────────────────────────

# --- League CRUD (Keep existing routes, ensure decorators are applied) ---
@admin.route("/leagues")
@login_required
@admin_required
def leagues():
    # ... (keep existing code) ...
    with SessionLocal() as db:
        rows = (db.query(DbLeague).options(selectinload(DbLeague.tasks)).order_by(DbLeague.name).all())
    return render_template("admin/leagues.html", leagues=rows)

@admin.route("/leagues/new", methods=["GET","POST"])
@login_required
@admin_required
def league_new():
    # ... (keep existing code) ...
    form = LeagueForm()
    if form.validate_on_submit():
        tmpl_lookup = {("league","yes"): "officiated_league", ("league","no"): "nonofficiated_league", ("tournament","yes"): "officiated_event", ("tournament","no"): "nonofficiated_event"}
        template_id = tmpl_lookup.get((form.kind.data, form.officiated.data))
        if not template_id: flash("Could not determine template ID.", "error"); return render_template("admin/league_form.html", form=form, mode="new")
        league = DbLeague(id=form.id.data, name=form.name.data, kind=form.kind.data, season_start=form.season_start.data, season_end=form.season_end.data, officiated=(form.officiated.data=="yes"), template_id=template_id)
        with SessionLocal() as db:
            if db.get(DbLeague, form.id.data): flash(f"League with ID '{form.id.data}' already exists.", "error"); return render_template("admin/league_form.html", form=form, mode="new")
            db.add(league); db.flush()
            tmpl_tasks = (db.query(DbTemplateTask).filter_by(template_id=template_id).order_by(DbTemplateTask.order).all())
            if not tmpl_tasks: flash(f"Warning: No template tasks found for template ID '{template_id}'.", "warning")
            resolved_due_dates = {}; new_tasks = []
            for t_tmpl in tmpl_tasks:
                abs_due = resolve_due(t_tmpl.relative_due, league.season_start, league.season_end, resolved_due_dates)
                resolved_due_dates[t_tmpl.task_ref_id] = abs_due
                new_task = DbTask(id=f"{league.id}_{t_tmpl.task_ref_id}", league_id=league.id, title=t_tmpl.title, category=t_tmpl.category, due=abs_due.date() if isinstance(abs_due, datetime) else (abs_due if isinstance(abs_due, date) else None), order=t_tmpl.order, instructions=t_tmpl.instructions,
                                  link_1_url=t_tmpl.link_1_url, link_1_label=t_tmpl.link_1_label, link_2_url=t_tmpl.link_2_url, link_2_label=t_tmpl.link_2_label, notes=t_tmpl.notes, contact_info=t_tmpl.contact_info, email_template_subject=t_tmpl.email_template_subject, email_template_body=t_tmpl.email_template_body, email_recipient_source=t_tmpl.email_recipient_source, email_target_address=t_tmpl.email_target_address, previous_report_link=t_tmpl.previous_report_link, improvement_goals=t_tmpl.improvement_goals, imleagues_staff_link=t_tmpl.imleagues_staff_link, offer_letter_template=t_tmpl.offer_letter_template, report_template_link=t_tmpl.report_template_link, pac_instructor_contact=t_tmpl.pac_instructor_contact, facilities_contact=t_tmpl.facilities_contact, facilities_booking_link=t_tmpl.facilities_booking_link, facilities_email_templates=t_tmpl.facilities_email_templates, imleagues_schedule_link=t_tmpl.imleagues_schedule_link, clinic_booking_link=t_tmpl.clinic_booking_link, zoom_meeting_link=t_tmpl.zoom_meeting_link, imleagues_paste_location_link=t_tmpl.imleagues_paste_location_link, inventory_list_link=t_tmpl.inventory_list_link, equipment_notes=t_tmpl.equipment_notes, rules_doc_link=t_tmpl.rules_doc_link, imleagues_rules_upload_link=t_tmpl.imleagues_rules_upload_link, presentation_slides_link=t_tmpl.presentation_slides_link, interest_list_link=t_tmpl.interest_list_link, whentowork_link=t_tmpl.whentowork_link, imleagues_messaging_link=t_tmpl.imleagues_messaging_link, participant_message_templates=t_tmpl.participant_message_templates, slides_template_link=t_tmpl.slides_template_link, captain_quiz_link=t_tmpl.captain_quiz_link, imleagues_email_link=t_tmpl.imleagues_email_link, spa_meeting_docs_link=t_tmpl.spa_meeting_docs_link, shirt_tracker_link=t_tmpl.shirt_tracker_link, flickr_link=t_tmpl.flickr_link, marketing_folder_link=t_tmpl.marketing_folder_link, jersey_checkin_link=t_tmpl.jersey_checkin_link, summary_report_template_link=t_tmpl.summary_report_template_link, summary_report_draft=t_tmpl.summary_report_draft)
                new_tasks.append(new_task)
            db.add_all(new_tasks)
            try: db.commit(); flash(f"League '{league.name}' created successfully with {len(new_tasks)} tasks.", "success")
            except Exception as e: db.rollback(); flash(f"Error creating league: {e}", "error"); print(f"Database Commit Error: {e}"); return render_template("admin/league_form.html", form=form, mode="new")
        return redirect(url_for("admin.leagues"))
    else:
        if request.method == 'POST':
            for field, errors in form.errors.items(): flash(f"Error in {getattr(form, field).label.text}: {errors[0]}", "error")
    return render_template("admin/league_form.html", form=form, mode="new")


@admin.route("/leagues/<lid>/edit", methods=["GET","POST"])
@login_required
@admin_required
def league_edit(lid):
    # ... (keep existing code) ...
    with SessionLocal() as db:
        league = db.query(DbLeague).options(selectinload(DbLeague.tasks)).filter(DbLeague.id == lid).first()
        if not league: abort(404)
        form = LeagueForm(obj=league)
        if form.validate_on_submit():
            league.name = form.name.data; league.season_start = form.season_start.data; league.season_end = form.season_end.data; league.kind = form.kind.data; league.officiated = (form.officiated.data == "yes")
            try: db.commit(); flash(f"League '{league.name}' updated successfully.", "success")
            except Exception as e: db.rollback(); flash(f"Error updating league: {e}", "error"); print(f"Database Commit Error: {e}")
            return redirect(url_for(".leagues"))
        elif request.method == 'POST':
            for field, errors in form.errors.items(): flash(f"Error in {getattr(form, field).label.text}: {errors[0]}", "error")
    return render_template("admin/league_form.html", form=form, mode="edit", league_name=league.name)

@admin.route("/leagues/<lid>/delete", methods=["POST"])
@login_required
@admin_required
def league_delete(lid):
    # ... (keep existing code) ...
     with SessionLocal() as db:
        league = db.get(DbLeague, lid)
        if league:
            try: db.delete(league); db.commit(); flash(f"League '{league.name}' deleted successfully.", "success")
            except Exception as e: db.rollback(); flash(f"Error deleting league: {e}", "error"); print(f"Database Commit Error: {e}")
        else: flash("League not found.", "error"); abort(404) # Abort if not found even on POST
     return redirect(url_for(".leagues"))

# --- Task CRUD (Keep existing routes, ensure decorators are applied) ---
@admin.route("/leagues/<lid>/tasks")
@login_required
@admin_required
def tasks(lid):
    # ... (keep existing code) ...
    league = get_league(lid);
    if not league: abort(404)
    return render_template("admin/tasks.html", league=league)

@admin.route("/leagues/<lid>/tasks/new", methods=["GET", "POST"])
@login_required
@admin_required
def task_new(lid):
    # ... (keep existing code) ...
    league = get_league(lid);
    if not league: abort(404)
    form = TaskForm()
    if form.validate_on_submit():
        full_task_id = f"{lid}_{form.id.data}"
        task = DbTask(id=full_task_id, league_id=lid)
        form.populate_obj(task); task.id=full_task_id; task.league_id=lid
        with SessionLocal() as db:
            if db.get(DbTask, full_task_id): flash(f"Task with ID '{form.id.data}' already exists for this league.", "error"); league_for_template = get_league(lid); return render_template("admin/task_form.html", league=league_for_template, form=form, mode="new")
            db.add(task)
            try: db.commit(); flash(f"Task '{task.title}' created successfully.", "success")
            except Exception as e: db.rollback(); flash(f"Error creating task: {e}", "error"); print(f"Database Commit Error: {e}"); league_for_template = get_league(lid); return render_template("admin/task_form.html", league=league_for_template, form=form, mode="new")
        return redirect(url_for("admin.tasks", lid=lid))
    else:
        if request.method == 'POST':
            for field, errors in form.errors.items(): flash(f"Error in {getattr(form, field).label.text}: {errors[0]}", "error")
    return render_template("admin/task_form.html", league=league, form=form, mode="new")


@admin.route("/leagues/<lid>/tasks/<tid>/edit", methods=["GET","POST"])
@login_required
@admin_required
def task_edit(lid, tid):
    # ... (keep existing code) ...
    with SessionLocal() as db:
        task = db.get(DbTask, tid)
        if not task or task.league_id != lid: flash("Task not found for this league.", "error"); abort(404)
        form = TaskForm(obj=task); form.id.render_kw = {'readonly': True}
        short_task_id = tid.split(f"{lid}_", 1)[-1] if tid.startswith(f"{lid}_") else tid
        if form.validate_on_submit():
            original_id = task.id; form.populate_obj(task); task.id = original_id; task.league_id = lid
            try: db.commit(); flash(f"Task '{task.title}' updated successfully.", "success")
            except Exception as e: db.rollback(); flash(f"Error updating task: {e}", "error"); print(f"Database Commit Error: {e}")
            return redirect(url_for(".tasks", lid=lid))
        elif request.method == 'POST':
            for field, errors in form.errors.items(): flash(f"Error in {getattr(form, field).label.text}: {errors[0]}", "error")
    league = get_league(lid);
    if not league: abort(404)
    return render_template("admin/task_form.html", league=league, form=form, mode="edit", task_id_display=short_task_id)


@admin.route("/leagues/<lid>/tasks/<tid>/delete", methods=["POST"])
@login_required
@admin_required
def task_delete(lid, tid):
    # ... (keep existing code) ...
    with SessionLocal() as db:
        task = db.get(DbTask, tid)
        if task and task.league_id == lid:
            try: db.delete(task); db.commit(); flash(f"Task '{task.title}' deleted successfully.", "success")
            except Exception as e: db.rollback(); flash(f"Error deleting task: {e}", "error"); print(f"Database Commit Error: {e}")
        else: flash("Task not found or does not belong to this league.", "error")
    return redirect(url_for(".tasks", lid=lid))


# --- NEW Club CRUD Routes ---

@admin.route("/clubs")
@login_required
@admin_required
def clubs():
    """List all clubs."""
    with SessionLocal() as db:
        all_clubs = db.query(DbClub).order_by(DbClub.name).all()
    return render_template("admin/clubs.html", clubs=all_clubs)

@admin.route("/clubs/new", methods=["GET", "POST"])
@login_required
@admin_required
def club_new():
    """Create a new club."""
    form = ClubForm()
    if form.validate_on_submit():
        new_club = DbClub(name=form.name.data, is_active=form.is_active.data)
        with SessionLocal() as db:
            db.add(new_club)
            try:
                db.commit()
                flash(f"Club '{new_club.name}' created successfully.", "success")
                return redirect(url_for(".clubs"))
            except Exception as e:
                db.rollback()
                flash(f"Error creating club: {e}", "danger")
                print(f"Database Commit Error (Club New): {e}")
    else:
         # Flash WTForms validation errors
        if request.method == 'POST':
            for field, errors in form.errors.items():
                flash(f"Error in {getattr(form, field).label.text}: {errors[0]}", "danger")

    return render_template("admin/club_form.html", form=form, mode="new", legend="Create New Club")


@admin.route("/clubs/<int:club_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def club_edit(club_id):
    """Edit an existing club."""
    with SessionLocal() as db:
        club = db.get(DbClub, club_id)
        if not club:
            flash("Club not found.", "error")
            abort(404)

        # Pass club object to form for pre-population
        # Pass the original object to the form's validate_name method
        form = ClubForm(obj=club)

        if form.validate_on_submit():
            # Populate club object with form data
            form.populate_obj(club)
            try:
                db.commit()
                flash(f"Club '{club.name}' updated successfully.", "success")
                return redirect(url_for(".clubs"))
            except Exception as e:
                db.rollback()
                flash(f"Error updating club: {e}", "danger")
                print(f"Database Commit Error (Club Edit): {e}")
        elif request.method == 'POST':
             # Flash WTForms validation errors
            for field, errors in form.errors.items():
                flash(f"Error in {getattr(form, field).label.text}: {errors[0]}", "danger")

    return render_template("admin/club_form.html", form=form, mode="edit", club_id=club_id, legend=f"Edit Club: {club.name}")

# Optional: Add a route to delete clubs if needed, be careful about FK constraints!
# @admin.route("/clubs/<int:club_id>/delete", methods=["POST"])
# @login_required
# @admin_required
# def club_delete(club_id):
#     with SessionLocal() as db:
#         club = db.get(DbClub, club_id)
#         if club:
#             # Check if club is linked to transactions before deleting?
#             # linked_transactions = db.query(FoundationTransaction).filter_by(club_id=club_id).count()
#             # if linked_transactions > 0:
#             #     flash(f"Cannot delete club '{club.name}' as it has associated transactions.", "warning")
#             #     return redirect(url_for('.clubs'))
#             try:
#                 db.delete(club)
#                 db.commit()
#                 flash(f"Club '{club.name}' deleted.", "success")
#             except Exception as e:
#                 db.rollback()
#                 flash(f"Error deleting club: {e}", "danger")
#         else:
#             flash("Club not found.", "error")
#     return redirect(url_for(".clubs"))

