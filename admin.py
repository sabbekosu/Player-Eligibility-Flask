from flask import Blueprint, render_template, redirect, url_for, request, abort
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, TextAreaField
from wtforms.validators import DataRequired
from db import SessionLocal
from models import League as DBLeague, Task as DBTask

from league_checklist import get_league 

admin = Blueprint("admin", __name__, url_prefix="/admin",
                  template_folder="templates")

# ── Forms ────────────────────────────────────────────────────────────────────
class LeagueForm(FlaskForm):
    id   = StringField("ID",   validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])

class TaskForm(FlaskForm):
    id    = StringField("ID", validators=[DataRequired()])
    title = StringField("Title", validators=[DataRequired()])
    category = SelectField("Category",
                           choices=[("Pre-League","Pre-League"),
                                    ("Post-League","Post-League")])
    due   = DateField("Due", format="%Y-%m-%d")
    order = StringField("Order")
    instructions = TextAreaField("Instructions")

# ── League CRUD ──────────────────────────────────────────────────────────────
@admin.route("/leagues")
def leagues():
    with SessionLocal() as db:
        rows = db.query(League).order_by(League.name).all()
    return render_template("admin/leagues.html", leagues=rows)

@admin.route("/leagues/new", methods=["GET","POST"])
def league_new():
    form = LeagueForm()
    if form.validate_on_submit():
        with SessionLocal() as db:
            db.add(League(id=form.id.data, name=form.name.data))
            db.commit()
        return redirect(url_for(".leagues"))
    return render_template("admin/league_form.html", form=form, mode="new")

@admin.route("/leagues/<lid>/edit", methods=["GET","POST"])
def league_edit(lid):
    with SessionLocal() as db:
        league = db.get(League, lid) or abort(404)
        form = LeagueForm(obj=league)
        if form.validate_on_submit():
            form.populate_obj(league)
            db.commit()
            return redirect(url_for(".leagues"))
    return render_template("admin/league_form.html", form=form, mode="edit")

@admin.route("/leagues/<lid>/delete", methods=["POST"])
def league_delete(lid):
    with SessionLocal() as db:
        league = db.get(League, lid) or abort(404)
        db.delete(league); db.commit()
    return redirect(url_for(".leagues"))

# ── Task CRUD (nested under league) ──────────────────────────────────────────
@admin.route("/leagues/<lid>/tasks")
def tasks(lid):
    league = get_league(lid) or abort(404)
    return render_template("admin/tasks.html", league=league)

@admin.route("/leagues/<lid>/tasks/new", methods=["GET","POST"])
def task_new(lid):
    league = get_league(lid) or abort(404)
    form = TaskForm()
    if form.validate_on_submit():
        with SessionLocal() as db:
            db.add(Task(league_id=lid, **form.data))
            db.commit()
        return redirect(url_for(".tasks", lid=lid))
    return render_template("admin/task_form.html", league=league, form=form, mode="new")

@admin.route("/leagues/<lid>/tasks/<tid>/edit", methods=["GET","POST"])
def task_edit(lid, tid):
    with SessionLocal() as db:
        task = db.get(Task, tid) or abort(404)
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
        task = db.get(Task, tid) or abort(404)
        db.delete(task); db.commit()
    return redirect(url_for(".tasks", lid=lid))
