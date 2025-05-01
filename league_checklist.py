# league_checklist.py
from __future__ import annotations

"""Blueprint that adds a league-management checklist workflow."""

from dataclasses import dataclass
from typing import Dict, List, Set
# Corrected Imports: SessionLocal from db, Progress from models
from db import SessionLocal
from models import Progress, League as DbLeague, Task as DbTask, User
# Import date from datetime
from datetime import datetime, date, time # Import time for combining date
from sqlalchemy.orm import selectinload, joinedload, Session
# Import login_required and current_user
from flask_login import login_required, current_user
# Import sys for maxsize (used in sorting None)
import sys


from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session, # Keep session if used elsewhere, but progress uses DB now
    url_for,
)

bp = Blueprint("leagues", __name__, template_folder="templates")

# ────────────────────────────────────────────────────────────────────────────────
# Data Access Helpers (using SQLAlchemy)
# ────────────────────────────────────────────────────────────────────────────────

def get_progress_set_for_user(league_id: str, user_id: int) -> Set[str]:
    """Gets the set of completed task IDs for a specific user and league."""
    with SessionLocal() as db:
        rows = (
            db.query(Progress.task_id)
              .filter_by(league_id=league_id, user_id=user_id) # Filter by user
              .all()
        )
        return {r[0] for r in rows}

# --- MODIFIED toggle_progress ---
@login_required # Require login to toggle progress
def toggle_progress(league_id: str, task_id: str):
    """Toggles the completion status of a task FOR THE CURRENT USER."""
    user_id = current_user.id # Get the current logged-in user's ID

    with SessionLocal() as db:
        # Composite primary key now includes user_id
        progress_pk = {"league_id": league_id, "task_id": task_id, "user_id": user_id}
        row = db.get(Progress, progress_pk)

        if row:
            # User has completed this task, mark as incomplete
            db.delete(row)
            action = "deleted"
        else:
            # User has not completed this task, mark as complete
            db.add(Progress(league_id=league_id,
                            task_id=task_id,
                            user_id=user_id, # Store the user ID
                            done_at=datetime.utcnow()))
            action = "added"
        try:
            db.commit()
            # print(f"Progress {action} for {league_id}/{task_id} by user {user_id}") # Debug log
        except Exception as e:
            db.rollback()
            print(f"Error toggling progress for {league_id}/{task_id} by user {user_id}: {e}")
            flash(f"Could not update task status. Please try again.", "danger")

# --- get_league and get_task (Unchanged) ---
def get_league(league_id: str) -> DbLeague | None:
    """Return League with tasks eagerly loaded using joinedload."""
    with SessionLocal() as db:
        return (
            db.query(DbLeague)
              .options(joinedload(DbLeague.tasks))
              .filter(DbLeague.id == league_id)
              .first()
        )

def get_task(task_id: str) -> DbTask | None:
    """Gets a single task by its full ID."""
    with SessionLocal() as db:
        return db.get(DbTask, task_id)

# ────────────────────────────────────────────────────────────────────────────────
# Routes
# ────────────────────────────────────────────────────────────────────────────────

@bp.route("/leagues")
@login_required # Users must be logged in to see leagues
def league_list():
    """Displays the list of all leagues."""
    with SessionLocal() as db:
        leagues = (
            db.query(DbLeague)
              .options(selectinload(DbLeague.tasks))
              .order_by(DbLeague.name)
              .all()
        )
    # Get progress for the CURRENT user
    progress_map = {lg.id: get_progress_set_for_user(lg.id, current_user.id) for lg in leagues}

    return render_template("leagues.html",
                           leagues=leagues,
                           progress=progress_map) # Pass user-specific progress

@bp.route("/leagues/<league_id>")
@login_required # Users must be logged in
def league_checklist(league_id):
    """Displays the checklist for a specific league."""
    league = get_league(league_id)
    if not league:
        abort(404)

    # Get progress for the CURRENT user
    progress = get_progress_set_for_user(league_id, current_user.id)
    today = date.today()

    # --- Group and Sort Tasks in Python ---
    ordered_categories = ["Pre-League", "Pre-Event", "Post-League", "Post-Event"]
    grouped_sorted_tasks = {cat: [] for cat in ordered_categories}

    # Define a sort key function
    def task_sort_key(task):
        # Handle None for order: treat as a large number to sort last among numbered items
        order_key = sys.maxsize
        if task.order:
            try:
                # Try converting to int for numeric sort, fallback to string
                order_key = int(task.order)
            except ValueError:
                order_key = task.order # Keep as string if not purely numeric

        # Handle None for due date: treat as infinitely far in the future
        due_key = task.due if task.due is not None else date.max

        # Return tuple for multi-level sorting
        # 1. Due Date (earliest first, None last)
        # 2. Order (numeric/string, None/non-numeric treated as large)
        # 3. Title (alphabetical)
        return (due_key, order_key, task.title or "")

    # Group tasks
    tasks_by_category = {}
    for task in league.tasks:
        tasks_by_category.setdefault(task.category, []).append(task)

    # Sort within each category
    for cat in ordered_categories:
        if cat in tasks_by_category:
            grouped_sorted_tasks[cat] = sorted(tasks_by_category[cat], key=task_sort_key)
    # --- End Group and Sort ---


    return render_template("checklist.html",
                           league=league, # Pass league for name etc.
                           progress=progress,
                           today_date=today,
                           # Pass the grouped and sorted tasks
                           grouped_tasks=grouped_sorted_tasks,
                           ordered_categories=ordered_categories)


@bp.route("/leagues/<league_id>/task/<task_id>", methods=["GET", "POST"])
@login_required # Users must be logged in
def league_task(league_id, task_id):
    """Displays details for a single task and handles completion toggle FOR THE CURRENT USER."""
    task = get_task(task_id)
    if not task or task.league_id != league_id:
        abort(404)

    # Fetch league object for league name in title/breadcrumbs if needed
    # Avoid loading all tasks again if not necessary
    with SessionLocal() as db:
        league_info = db.query(DbLeague.name).filter(DbLeague.id == league_id).first()
    if not league_info: abort(404)


    today = date.today() # Get today's date for overdue check

    if request.method == "POST":
        # Call the modified toggle_progress (which uses current_user implicitly)
        toggle_progress(league_id, task_id)
        # Redirect back to the main checklist
        return redirect(url_for("leagues.league_checklist", league_id=league_id))

    # GET request: Display the task details
    # Check completion status FOR THE CURRENT USER
    completed = task_id in get_progress_set_for_user(league_id, current_user.id)

    return render_template("task.html",
                           league_id=league_id, # Pass ID for back button
                           league_name=league_info.name, # Pass name for display
                           task=task,
                           completed=completed,
                           today_date=today)


@bp.route("/leagues/<league_id>/task/<task_id>/generate_summary_snippet", methods=["POST"])
@login_required # Secure this endpoint too
def generate_summary_snippet(league_id, task_id):
    """
    API endpoint called by JavaScript to generate summary report snippets.
    (Code for gathering data and populating template remains the same as previous version)
    """
    # ... (Keep existing code from previous version for generating snippet) ...
    if not task_id.endswith("_summary_report"):
         return "Invalid task for summary generation.", 400
    summary_task = get_task(task_id)
    # Need full league object here to iterate through tasks for context
    league = get_league(league_id)
    if not summary_task or not league or summary_task.league_id != league_id:
        return "Task or League not found.", 404
    template_draft = summary_task.summary_report_draft or ""
    if not template_draft:
        template_draft = "# Summary Report Snippets\n## Goals:\n{improvement_goals}\n## Equipment Notes:\n{equipment_notes}\n## Challenges:\n\n## Recommendations:\n"
    context = {
        'improvement_goals': "No goals task found or goals not set.",
        'equipment_notes': "No equipment task found or notes not set.",
    }
    for t in league.tasks:
        if t.id.endswith("_review_reports") or t.id.endswith("_create_goals"):
            if t.improvement_goals:
                 if context['improvement_goals'] == "No goals task found or goals not set.":
                     context['improvement_goals'] = t.improvement_goals
        if t.id.endswith("_check_equipment") or t.id.endswith("_notify_equipment"):
             if t.equipment_notes:
                 if context['equipment_notes'] == "No equipment task found or notes not set.":
                     context['equipment_notes'] = t.equipment_notes
    try:
        populated_snippet = template_draft.format(**context)
    except KeyError as e:
        print(f"Warning: Placeholder {e} not found in context for summary snippet.")
        populated_snippet = template_draft
    # Update Task in DB
    with SessionLocal() as db:
        task_to_update = db.get(DbTask, task_id)
        if task_to_update:
            task_to_update.summary_report_draft = populated_snippet
            try: db.commit()
            except Exception as e:
                db.rollback()
                print(f"Error saving generated summary snippet: {e}")
    return populated_snippet, 200
