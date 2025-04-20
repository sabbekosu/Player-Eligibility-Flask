from __future__ import annotations

import json
import re
import uuid
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Dict, List, Set

import fitz  # PyMuPDF
import pandas as pd
import pdfplumber
from bs4 import BeautifulSoup
from flask import Flask, flash, redirect, render_template, request, url_for
from pdfminer.high_level import extract_text_to_fp

# ────────────────────────────────────────────────────────────────────────────────
# Paths & Flask setup
# ────────────────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent
ROSTER_DIR = BASE_DIR / "club_rosters"
ROSTER_META = ROSTER_DIR / "rosters.json"
ROSTER_DIR.mkdir(exist_ok=True)

app = Flask(__name__, template_folder=str(BASE_DIR / "templates"))
app.secret_key = "replace‑me"  # set securely in production

# ────────────────────────────────────────────────────────────────────────────────
# Helpers for roster persistence
# ────────────────────────────────────────────────────────────────────────────────

def _load_meta() -> Dict[str, Dict]:
    if ROSTER_META.exists():
        try:
            return json.loads(ROSTER_META.read_text())
        except json.JSONDecodeError:
            flash("⚠️ roster metadata corrupted; reset (backup saved).")
            ROSTER_META.rename(ROSTER_META.with_suffix(".bak"))
    return {}


def _save_meta(meta: Dict):
    ROSTER_META.write_text(json.dumps(meta, indent=2))


def _safe_filename(club_name: str, original_name: str) -> str:
    base = club_name.strip().lower().replace(" ", "_") or Path(original_name).stem
    ts   = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{base}_{ts}.csv"


def save_or_replace_roster(file_storage, club_name: str) -> Path:
    """Save CSV, *replacing* any prior roster for the same club.

    • If a roster with the same club_name (case‑insensitive) exists, its file is
      deleted and the metadata entry is updated (keeps the same roster_id).
    • Otherwise a new roster_id is created.
    Returns Path to the saved CSV (new file).
    """
    meta = _load_meta()

    # find existing id for club (case‑insensitive match)
    existing_id = next((rid for rid, data in meta.items()
                        if data["club_name"].lower() == club_name.lower()), None)

    fname = _safe_filename(club_name, file_storage.filename)
    dest  = ROSTER_DIR / fname
    file_storage.save(dest)

    now_iso = datetime.now().isoformat(timespec="seconds")

    if existing_id:
        # delete the old file
        old_path = ROSTER_DIR / meta[existing_id]["filename"]
        if old_path.exists():
            old_path.unlink()
        # update existing metadata
        meta[existing_id]["filename"]   = fname
        meta[existing_id]["uploaded_at"] = now_iso
        roster_id = existing_id
    else:
        roster_id = str(uuid.uuid4())
        meta[roster_id] = {
            "club_name":  club_name,
            "filename":   fname,
            "uploaded_at": now_iso,
        }

    _save_meta(meta)
    return dest

# ────────────────────────────────────────────────────────────────────────────────
# PDF text extraction (unchanged)
# ────────────────────────────────────────────────────────────────────────────────

def extract_text_pdfplumber(file_obj):
    try:
        file_obj.seek(0)
        with pdfplumber.open(file_obj) as pdf:
            text = "\n".join([(p.extract_text() or "") for p in pdf.pages])
            if text.strip():
                return text
    except Exception as e:
        flash(f"⚠️ pdfplumber failed: {e}")
    return None


def extract_text_pymupdf(file_obj):
    try:
        file_obj.seek(0)
        pdf_bytes = file_obj.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = "\n".join([page.get_text("text") for page in doc])
        doc.close()
        if text.strip():
            return text
    except Exception as e:
        flash(f"⚠️ PyMuPDF failed: {e}")
    return None


def extract_text_html(file_obj):
    try:
        file_obj.seek(0)
        buff = StringIO()
        extract_text_to_fp(file_obj, buff, output_type="html")
        text = BeautifulSoup(buff.getvalue(), "html.parser").get_text()
        if text.strip():
            return text
    except Exception as e:
        flash(f"⚠️ HTML extraction failed: {e}")
    return None

# ────────────────────────────────────────────────────────────────────────────────
# Club CSV → player name set helper
# ────────────────────────────────────────────────────────────────────────────────

def build_club_player_set(csv_source) -> Set[str]:
    try:
        df = pd.read_csv(csv_source, skiprows=3)
        df = df[df["Status"].str.strip().str.upper() == "OK"]
        df["Full Name"] = df["Person"].apply(lambda x: " ".join(x.strip().lower().split(", ")[::-1]))
        return set(df["Full Name"].tolist())
    except Exception as e:
        flash(f"Error processing club roster {csv_source}: {e}")
        return set()

# ────────────────────────────────────────────────────────────────────────────────
# Main route
# ────────────────────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET", "POST"])
def index():
    saved_rosters = _load_meta()
    sorted_rosters = sorted(saved_rosters.items(), key=lambda item: item[1]["club_name"].lower())

    if request.method == "POST":
        player_limit      = request.form.get("player_limit", "5 or fewer")
        max_club_players  = 1 if "5 or fewer" in player_limit else 2
        club_players: Set[str] = set()

        # 1. existing saved selections (hidden inputs inside chips)
        for rid in request.form.getlist("existing_rosters"):
            if rid not in saved_rosters:
                flash(f"Unknown roster id {rid}")
                continue
            club_players.update(build_club_player_set(ROSTER_DIR / saved_rosters[rid]["filename"]))

        # 2. new CSV uploads + selected/other club names
        uploaded_csvs = request.files.getlist("club_csvs")
        club_names_in_form = request.form.getlist("club_names[]")
        other_names        = request.form.getlist("other_club_names[]")  # may come from JS later

        for idx, fs in enumerate(uploaded_csvs):
            if not fs or not fs.filename:
                continue
            club_name = club_names_in_form[idx] if idx < len(club_names_in_form) else "Other"
            if club_name == "Other" and idx < len(other_names) and other_names[idx].strip():
                club_name = other_names[idx].strip()
            club_path = save_or_replace_roster(fs, club_name)
            club_players.update(build_club_player_set(club_path))

        # 3. PDF
        im_pdf = request.files.get("im_pdf")
        if not im_pdf or not im_pdf.filename:
            flash("Please upload an IM Team Rosters PDF.")
            return render_template("index.html", saved_rosters=saved_rosters, sorted_rosters=sorted_rosters)

        text = (
            extract_text_pdfplumber(im_pdf)
            or extract_text_pymupdf(im_pdf)
            or extract_text_html(im_pdf)
        )
        if not text:
            flash("❌ Failed to extract text from PDF.")
            return render_template("index.html", saved_rosters=saved_rosters, sorted_rosters=sorted_rosters)

        # 4. parse teams (same as before)
        teams: Dict[str, List[str]] = {}
        elite_players: Set[str] = set()
        elite_teams: Dict[str, str] = {}
        current_team = None
        recording_players = False
        current_level = "Regular"
        for line in text.split("\n"):
            if (
                "Oregon State University" in line
                or "imleagues.com" in line
                or re.match(r"\d{1,2}/\d{1,2}/\d{2}, \d{1,2}:\d{2} [APap][Mm]", line)
            ):
                continue
            if "->" in line:
                current_level = "Elite" if "Elite" in line else "Regular"
                continue
            m = re.match(r"(.+?)Rosters", line)
            if m:
                current_team = m.group(1).strip()
                teams[current_team] = []
                if current_level == "Elite":
                    elite_teams[current_team] = "Elite"
                recording_players = False
                continue
            if "Name Gender Status" in line:
                recording_players = True
                continue
            if recording_players and line.strip():
                p = line.split(" Male ")[0].split(" Female ")[0].strip()
                p = re.sub(r"^C-", "", p, flags=re.IGNORECASE)
                p = re.sub(r"\(Nomad\)$", "", p, flags=re.IGNORECASE)
                p = p.lower()
                if current_team in elite_teams:
                    elite_players.add(p)
                if current_team:
                    teams[current_team].append(p)

        club_players.update(elite_players)
        violations: Dict[str, int] = {}
        team_club_members: Dict[str, List[str]] = {}
        for team, roster in teams.items():
            if team in elite_teams:
                continue
            club_on_team = [player.title() for player in roster if player in club_players]
            team_club_members[team] = club_on_team
            if len(club_on_team) > max_club_players:
                violations[team] = len(club_on_team)

        return render_template(
            "results.html",
            max_club_players=max_club_players,
            violations=violations,
            team_club_members=team_club_members,
        )

    # GET path
    return render_template("index.html", saved_rosters=saved_rosters, sorted_rosters=sorted_rosters)

# ────────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
