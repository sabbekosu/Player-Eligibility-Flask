from flask import Blueprint, render_template, redirect, url_for, request, abort
from flask_wtf import FlaskForm
import re
from wtforms import StringField, SelectField, DateField, TextAreaField
from wtforms.validators import DataRequired
from db import SessionLocal
from models import League as DBLeague, Task as DBTask, TemplateTask
from sqlalchemy.orm import selectinload
from datetime import timedelta

from league_checklist import get_league 

admin = Blueprint("admin", __name__, url_prefix="/admin",
                  template_folder="templates")

# ── Forms ────────────────────────────────────────────────────────────────────
class LeagueForm(FlaskForm):
    id   = StringField("ID", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    season_start = DateField("Season start", format="%Y-%m-%d")
    season_end   = DateField("Season end",   format="%Y-%m-%d")
    kind = SelectField("Kind", choices=[("league","League"),("tournament","Tournament")])
    officiated = SelectField("Officials", choices=[("yes","Officiated"),("no","Non-officiated")])


class TaskForm(FlaskForm):
    id    = StringField("ID", validators=[DataRequired()])
    title = StringField("Title", validators=[DataRequired()])
    category = SelectField("Category",
                           choices=[("Pre-League","Pre-League"),
                                    ("Post-League","Post-League")])
    due   = DateField("Due", format="%Y-%m-%d")
    order = StringField("Order")
    instructions = TextAreaField("Instructions")

def resolve_due(token, season_start, season_end, task_lookup=None):
    """
    Translate a compact due-date token into an absolute date.
      W-3          → 3 weeks before season_start
      D-10         → 10 days before season_start
      W+1e         → 1 week  after  season_end
      D+2t:task_id → 2 days  after  the absolute date of task_id
    """
    if not token:
        return None
    if task_lookup is None:
        task_lookup = {}

    # --- weeks relative to season start / end ------------------------------
    m = re.match(r"W([-+])(\d+)(e?)$", token, re.I)
    if m and season_start:
        sign, num, to_end = m.groups()
        num = int(num)
        base = season_end if to_end else season_start
        delta = timedelta(weeks=num)
        return base + delta if sign == "+" else base - delta

    # --- days relative to season start / end -------------------------------
    m = re.match(r"D([-+])(\d+)(e?)$", token, re.I)
    if m and season_start:
        sign, num, to_end = m.groups()
        num = int(num)
        base = season_end if to_end else season_start
        delta = timedelta(days=num)
        return base + delta if sign == "+" else base - delta

    # --- days after another task ------------------------------------------
    m = re.match(r"D\+(\d+)t:(\w+)", token, re.I)
    if m:
        days, dep = m.groups()
        base = task_lookup.get(dep)
        if base:
            return base + timedelta(days=int(days))

    # fallback – unknown pattern
    return None


# ── League CRUD ──────────────────────────────────────────────────────────────
@admin.route("/leagues")
def leagues():
    with SessionLocal() as db:
        rows = (
            db.query(DBLeague)
              .options(selectinload(DBLeague.tasks))   # eager-load
              .order_by(DBLeague.name)
              .all()
        )
    return render_template("admin/leagues.html", leagues=rows)

@admin.route("/leagues/new", methods=["GET","POST"])
def league_new():
    form = LeagueForm()
    if form.validate_on_submit():
        tmpl_lookup = {
            ("league","yes"):  "officiated_league",
            ("league","no"):   "nonofficiated_league",
            ("tournament","yes"):"officiated_event",
            ("tournament","no"): "nonofficiated_event",
        }
        template_id = tmpl_lookup[(form.kind.data, form.officiated.data)]

        league = DBLeague(
            id=form.id.data,
            name=form.name.data,
            kind=form.kind.data,
            season_start=form.season_start.data,
            season_end=form.season_end.data,
            officiated=(form.officiated.data=="yes"),
            template_id=template_id,
        )

        with SessionLocal() as db:
            db.add(league)
            # clone tasks from template
            tmpl_tasks = (
                db.query(TemplateTask)
                  .filter_by(template_id=template_id)
                  .all()
            )
            task_lookup = {}
            for t in tmpl_tasks:
                abs_due = resolve_due(t.relative_due,
                          league.season_start,
                          league.season_end,
                          task_lookup)
                db.add(DBTask(
                    id=f"{league.id}_{t.id}",
                    league_id=league.id,
                    title=t.title,
                    category=t.category,
                    due=abs_due,             # will compute later
                    order=t.order,
                    instructions=t.instructions,
                ))
                task_lookup[t.id] = abs_due
            db.commit()
        return redirect(url_for("admin.leagues"))

    return render_template("admin/league_form.html", form=form, mode="new")


@admin.route("/leagues/<lid>/edit", methods=["GET","POST"])
def league_edit(lid):
    with SessionLocal() as db:
        league = db.get(DBLeague, lid) or abort(404)
        form = LeagueForm(obj=league)
        if form.validate_on_submit():
            form.populate_obj(league)
            db.commit()
            return redirect(url_for(".leagues"))
    return render_template("admin/league_form.html", form=form, mode="edit")

@admin.route("/leagues/<lid>/delete", methods=["POST"])
def league_delete(lid):
    with SessionLocal() as db:
        league = db.get(DBLeague, lid) or abort(404)
        db.delete(league); db.commit()
    return redirect(url_for(".leagues"))

# ── Task CRUD (nested under league) ──────────────────────────────────────────
@admin.route("/leagues/<lid>/tasks")
def tasks(lid):
    league = get_league(lid) or abort(404)
    return render_template("admin/tasks.html", league=league)

@admin.route("/leagues/<lid>/tasks/new", methods=["GET", "POST"])
def task_new(lid):
    league = get_league(lid) or abort(404)
    form = TaskForm()

    if form.validate_on_submit():
        task = DBTask(
            id=form.id.data,
            league_id=lid,
            title=form.title.data,
            category=form.category.data,
            due=form.due.data,
            order=form.order.data,
            instructions=form.instructions.data,
        )
        with SessionLocal() as db:
            db.add(task)
            db.commit()
        return redirect(url_for("admin.tasks", lid=lid))

    return render_template("admin/task_form.html",
                           league=league,
                           form=form,
                           mode="new")

@admin.route("/leagues/<lid>/tasks/<tid>/edit", methods=["GET","POST"])
def task_edit(lid, tid):
    with SessionLocal() as db:
        task = db.get(DBTask, tid) or abort(404)
        form = TaskForm(obj=task)
        if form.validate_on_submit():
            form.populate_obj(task)
            db.commit()
            return redirect(url_for(".tasks", lid=lid))
    league = get_league(lid)
    return render_template("admin/task_form.html", league=league, form=form, mode="edit")

@admin.route("/leagues/<lid>/tasks/<tid>/delete", methods=["POST"])
def task_delete(lid, tid):
    with SessionLocal() as db:
        task = db.get(DBTask, tid) or abort(404)
        db.delete(task); db.commit()
    return redirect(url_for(".tasks", lid=lid))

@admin.route("/leagues/<lid>/import_demo", methods=["POST"])
def import_demo_tasks(lid):
    league = get_league(lid) or abort(404)

    pre_demo = [
        ("review_reports","Review previous year's summary reports","1 week before registration opens",
        "Locate last year's summary reports in the shared drive, read key findings, and write down 2-3 improvement goals."),
        ("email_officials","Email past officials and new applicants","4 weeks before officials training",
        "Send the invitation email template to returning & prospective officials."),
        ("hire_officials","Hire desired officials","4 weeks before first games",
        "Confirm hiring decisions in IMLeagues and send offer letters."),
        ("create_goals","Create goals on new summary report","3 weeks before event",
        "Open blank summary report and fill measurable goals."),
        ("schedule_pac","Communicate with instructor & schedule PAC appearance","3 weeks before reg deadline",
        "Email PAC213 instructor to book 10-minute class pitch."),
        ("check_facilities","Coordinate with facilities/ops staff","2 weeks before reg deadline",
        "Verify field lining and lights schedule."),
        ("mazevo_reserve","Reserve space in Mazevo","2 weeks before officials training",
        "Ensure every match slot in Mazevo matches IMLeagues."),
        ("confirm_clinic","Confirm officials clinic details","2 weeks before officials training",
        "Verify room booking and remind presenters."),
        ("setup_zoom","Set up Zoom manager's meeting link","2 weeks before reg deadline",
        "Create Zoom and paste link in IMLeagues."),
        ("equipment","Ensure we have all equipment","2 weeks before games start",
        "Inventory balls, cones; raise PO if needed."),
        ("rules_review","Review & upload rules","1 week before officials training",
        "Update rule tweaks, upload PDF to IMLeagues."),
        ("attend_pac","Attend and present to PAC class(es)","End of week 1",
        "Deliver 10-minute presentation & collect interest list."),
        ("schedule_spas","Schedule SPAs","End of week 1","Create shifts in WhenToWork."),
        ("message_past","Message past participants","End of week 1","Bulk-message last year's teams."),
        ("managers_ppt","Create manager's meeting powerpoint","Friday of week 1",
        "Duplicate last term's deck, update dates."),
        ("reminder_managers","Send reminder of manager's meeting","Day before meeting",
        "Send one-click email in IMLeagues."),
        ("club_check","Run Sport Club participation check","Registration deadline",
        "Use club eligibility checker tool."),
        ("meet_spas","Meet SPAs at fields/courts","Registration deadline",
        "Walk SPAs through setup and teardown."),
    ]

    post_demo = [
        ("shirts_photos","Distribute champ shirts & take photos","After final","Hand shirts, shoot photo, upload to Flickr."),
        ("equip_needs","Notify Macer/Tony of equipment needs","After final","Email replacement list."),
        ("post_photos","Post playoff & champ photos on Flickr","After final","Tag and add to album."),
        ("add_marketing","Add champ photos to Marketing folder","After final","Copy originals to Marketing/Champions/<term>."),
        ("update_tracker","Update Champion T-Shirt Tracker","After final","Update Google Sheet quantities."),
        ("collect_jerseys","Collect officials' jerseys","After final","Check-in list; invoice missing jerseys."),
        ("summary_report","Complete the summary report","After final","Finish summary and share with supervisor."),
    ]

    with SessionLocal() as db:
        for _id, title, due, instr in [*pre_demo, *post_demo]:
            if db.get(DBTask, _id):        # skip if already exists
                continue
            db.add(DBTask(id=_id, league_id=lid, title=title,
                        category="Pre-League" if (_id in dict(pre_demo)) else "Post-League",
                        due=None,
                        order=_id,
                        instructions=f"(Due {due}) — {instr}"))
        db.commit()
    return redirect(url_for("admin.tasks", lid=lid))

