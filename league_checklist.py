from __future__ import annotations

"""Blueprint that adds a league-management checklist workflow.

Prototype scope
================
* **No database** – league data and progress live in memory / Flask session so
  the feature is 100 % portable (works inside your PyInstaller bundle later).
* **Single demo league** (Soccer) with tasks copied from your “Officiated League
  Checklist” document.
* **Three routes**
    - `/leagues` – list the user's leagues + progress metrics
    - `/leagues/<league_id>` – interactive checklist
    - `/leagues/<league_id>/task/<task_id>` – details + mark complete/incomplete
* Extendable: just add more entries to ``LEAGUES`` or swap the in-memory dict
  for a database/ORM once you're ready.
"""

from dataclasses import dataclass
from typing import Dict, List
from db import SessionLocal, Progress
from datetime import datetime
from models import League as DBLeague, Task as DBTask
from sqlalchemy.orm import selectinload


from flask import (
    Blueprint,
    abort,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

bp = Blueprint("leagues", __name__, template_folder="templates")

# ────────────────────────────────────────────────────────────────────────────────
# Data model (in-memory)
# ────────────────────────────────────────────────────────────────────────────────
'''
@dataclass(frozen=True)
class Task:
    id: str
    title: str
    category: str  # "Pre-League" | "Post-League" | …
    due: str
    instructions: str


@dataclass(frozen=True)
class League:
    name: str
    tasks: List[Task]


def _soccer_tasks() -> List[Task]:
    """Return the Soccer League task list. Pulled out so you can re-use the
    same checklist skeleton for other sports later (copy/paste & tweak)."""

    pre = [
        ("review_reports", "Review previous year's summary reports", "1 week before registration opens", "Locate last year's summary reports in the shared drive, read key findings, and write down 2-3 improvement goals."),
        ("email_officials", "Email past officials and new applicants", "4 weeks before officials training", "Send the standard invitation email (see *templates/officials_invite.md*) to every official that worked last year plus anyone who has applied via Handshake."),
        ("hire_officials", "Hire desired officials", "4 weeks before first games", "Confirm hiring decisions in IMLeagues and send offer letters."),
        ("create_goals", "Create goals on new summary report", "3 weeks before event", "Open the blank seasonal summary report and fill in the measurable goals for this league."),
        ("schedule_pac", "Communicate with instructor & schedule PAC class appearance", "3 weeks before registration deadline", "Email the PAC213 instructor to book a 10-minute class pitch."),
        ("check_facilities", "Coordinate with facilities/operations staff as needed", "2 weeks before registration deadline", "Double-check field lining schedules and lights with Facilities."),
        ("mazevo_reserve", "Reserve space in Mazevo", "2 weeks before officials training", "Ensure every match slot exists in Mazevo and matches IMLeagues times."),
        ("confirm_clinic", "Confirm officials clinic details", "2 weeks before officials training", "Verify room booking and send reminder to presenters."),
        ("setup_zoom", "Set up Zoom manager's meeting link", "2 weeks before registration deadline", "Create Zoom, copy link into IMLeagues description."),
        ("equipment", "Ensure we have all equipment", "2 weeks before games start", "Inventory balls, keeper gloves, cones. Raise PO if short."),
        ("rules_review", "Review & upload rules", "1 week before officials training", "Update any rule tweaks, export PDF, replace file on IMLeagues."),
        ("attend_pac", "Attend and present to PAC class(es)", "End of week 1", "Deliver 10-minute presentation and collect interest list."),
        ("schedule_spas", "Schedule SPAs", "End of week 1", "Create shifts in WhenToWork and invite SPAs."),
        ("message_past", "Message past participants", "End of week 1", "Bulk-message last year's teams via IMLeagues marketing tool."),
        ("managers_ppt", "Create manager's meeting powerpoint", "Friday of week 1", "Duplicate last term's deck and update dates/captain quiz link."),
        ("reminder_managers", "Send reminder of manager's meeting", "Day before manager's meeting", "One-click email inside IMLeagues."),
        ("club_check", "Run Sport Club participation check", "Registration deadline", "Use the club eligibility checker tool :-) to flag excessive club members."),
        ("meet_spas", "Meet SPAs at fields/courts", "Registration deadline", "Walk through setup / teardown and on-field expectations."),
    ]

    post = [
        ("shirts_photos", "Distribute champ shirts & take photos", "After final", "Hand shirts, shoot photo, upload to Flickr."),
        ("equip_needs", "Notify Macer/Tony of equipment needs", "After final", "Email the replacement list."),
        ("post_photos", "Post playoff & champ photos on Flickr", "After final", "Tag and add to album."),
        ("add_marketing", "Add champ photos to Marketing folder", "After final", "Copy Flickr originals to Marketing/Champions/<term>."),
        ("update_tracker", "Update Champion T-Shirts Tracker", "After final", "Open Google Sheet and record quantities."),
        ("collect_jerseys", "Collect officials' jerseys", "After final", "Check-in list, send invoice to any missing jerseys."),
        ("summary_report", "Complete the summary report", "After final", "Finish seasonal summary document and share with supervisor."),
    ]

    return [
        *(Task(i, t, "Pre-League", d, instr) for i, t, d, instr in pre),
        *(Task(i, t, "Post-League", d, instr) for i, t, d, instr in post),
    ]


LEAGUES: Dict[str, League] = {
    "soccer": League(name="Soccer League", tasks=_soccer_tasks()),
}
'''
# ────────────────────────────────────────────────────────────────────────────────
# Session helper (replace with DB later)
# ────────────────────────────────────────────────────────────────────────────────

def get_progress_set(league_id: str) -> set[str]:
    with SessionLocal() as db:
        rows = (
            db.query(Progress.task_id)
              .filter_by(league_id=league_id)
              .all()
        )
        return {r[0] for r in rows}

def toggle_progress(league_id: str, task_id: str):
    with SessionLocal() as db:
        row = db.get(Progress, {"league_id": league_id, "task_id": task_id})
        if row:
            db.delete(row)
        else:
            db.add(Progress(league_id=league_id,
                            task_id=task_id,
                            done_at=datetime.utcnow()))
        db.commit()

def get_league(league_id: str) -> DBLeague | None:
    """Return League with tasks eagerly loaded (safe outside session)."""
    with SessionLocal() as db:
        return (
            db.query(DBLeague)
              .options(selectinload(DBLeague.tasks))
              .get(league_id)
        )


# ────────────────────────────────────────────────────────────────────────────────
# Routes
# ────────────────────────────────────────────────────────────────────────────────

@bp.route("/leagues")
def league_list():
    with SessionLocal() as db:
        leagues = (
            db.query(DBLeague)
              .options(selectinload(DBLeague.tasks))   # eager-load tasks
              .order_by(DBLeague.name)
              .all()
        )
    progress_map = {l.id: get_progress_set(l.id) for l in leagues}
    return render_template("leagues.html",
                           leagues=leagues,
                           progress=progress_map)

@bp.route("/leagues/<league_id>")
def league_checklist(league_id):
    league = get_league(league_id) or abort(404)
    progress = get_progress_set(league_id)
    return render_template("checklist.html",
                           league=league,
                           progress=progress)

@bp.route("/leagues/<league_id>/task/<task_id>", methods=["GET", "POST"])
def league_task(league_id, task_id):
    league = get_league(league_id) or abort(404)
    task   = next((t for t in league.tasks if t.id == task_id), None) or abort(404)

    if request.method == "POST":
        toggle_progress(league_id, task_id)
        return redirect(url_for("leagues.league_checklist", league_id=league_id))

    completed = task_id in get_progress_set(league_id)
    return render_template("task.html",
                           league=league,
                           task=task,
                           completed=completed)