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
from flask import Flask, flash, redirect, render_template, request, url_for, session # Added session
# Import Flask-Login components
from flask_login import LoginManager, current_user

from pdfminer.high_level import extract_text_to_fp

# Import Blueprints
from league_checklist import bp as leagues_bp
from admin import admin as admin_bp
from auth import auth as auth_bp # Import the new auth blueprint
from sports_clubs import sc_bp as sports_clubs_bp

# Import models (especially User for user_loader) and SessionLocal
from db import SessionLocal
from models import User

# ────────────────────────────────────────────────────────────────────────────────
# Paths & Flask setup
# ────────────────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent
ROSTER_DIR = BASE_DIR / "club_rosters"
ROSTER_META = ROSTER_DIR / "rosters.json"
UPLOAD_FOLDER = BASE_DIR / 'uploads' # Define upload folder path

ROSTER_DIR.mkdir(exist_ok=True)
UPLOAD_FOLDER.mkdir(exist_ok=True) # Create uploads folder if it doesn't exist

app = Flask(__name__, template_folder=str(BASE_DIR / "templates"))
app.temp_file_buffers = {}
app.secret_key = "replace-this-with-a-real-secret-key" # IMPORTANT: Change for production
# Configure the upload folder
app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)


# Register Blueprints
app.register_blueprint(leagues_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(sports_clubs_bp) # Register the sports_clubs blueprint

# --- Flask-Login Setup (Keep existing) ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    """Flask-Login hook to load a user object from the database."""
    with SessionLocal() as db:
        return db.query(User).get(int(user_id))
# -------------------------

# ────────────────────────────────────────────────────────────────────────────────
# Context Processor - Make current_user available to all templates
# ────────────────────────────────────────────────────────────────────────────────
@app.context_processor
def inject_user():
    return dict(current_user=current_user)

# ────────────────────────────────────────────────────────────────────────────────
# Roster Persistence Helpers (Unchanged)
# ────────────────────────────────────────────────────────────────────────────────
def _load_meta() -> Dict[str, Dict]:
    if ROSTER_META.exists():
        try:
            return json.loads(ROSTER_META.read_text())
        except json.JSONDecodeError:
            flash("⚠️ roster metadata corrupted; reset (backup saved).", "warning")
            ROSTER_META.rename(ROSTER_META.with_suffix(".bak"))
    return {}

def _save_meta(meta: Dict):
    ROSTER_META.write_text(json.dumps(meta, indent=2))

def _safe_filename(club_name: str, original_name: str) -> str:
    base = re.sub(r'[^\w\-]+', '_', club_name.strip().lower()) or Path(original_name).stem
    ts   = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{base}_{ts}.csv"

def save_or_replace_roster(file_storage, club_name: str) -> Path | None:
    """Save CSV, *replacing* any prior roster for the same club."""
    if not file_storage or not file_storage.filename:
        return None

    meta = _load_meta()
    existing_id = next((rid for rid, data in meta.items()
                        if data["club_name"].lower() == club_name.lower()), None)

    fname = _safe_filename(club_name, file_storage.filename)
    dest  = ROSTER_DIR / fname
    try:
        file_storage.save(dest)
    except Exception as e:
        flash(f"Error saving file {fname}: {e}", "danger")
        return None


    now_iso = datetime.now().isoformat(timespec="seconds")

    if existing_id:
        old_filename = meta[existing_id].get("filename")
        if old_filename:
             old_path = ROSTER_DIR / old_filename
             if old_path.exists() and old_path != dest: # Avoid deleting the file we just saved
                 try:
                    old_path.unlink()
                 except OSError as e:
                     print(f"Warning: Could not delete old roster file {old_path}: {e}")
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
# PDF Extraction Helpers (Unchanged)
# ────────────────────────────────────────────────────────────────────────────────
def extract_text_pdfplumber(file_obj):
    # ... (keep existing code) ...
    try:
        file_obj.seek(0)
        with pdfplumber.open(file_obj) as pdf:
            text = "\n".join([(p.extract_text() or "") for p in pdf.pages])
            if text.strip():
                return text
    except Exception as e:
        flash(f"⚠️ pdfplumber failed: {e}", "warning")
    return None

def extract_text_pymupdf(file_obj):
    # ... (keep existing code) ...
    try:
        file_obj.seek(0)
        pdf_bytes = file_obj.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = "\n".join([page.get_text("text") for page in doc])
        doc.close()
        if text.strip():
            return text
    except Exception as e:
        flash(f"⚠️ PyMuPDF failed: {e}", "warning")
    return None

def extract_text_html(file_obj):
    # ... (keep existing code) ...
    try:
        file_obj.seek(0)
        buff = StringIO()
        extract_text_to_fp(file_obj, buff, output_type="html")
        text = BeautifulSoup(buff.getvalue(), "html.parser").get_text()
        if text.strip():
            return text
    except Exception as e:
        flash(f"⚠️ HTML extraction failed: {e}", "warning")
    return None

# ────────────────────────────────────────────────────────────────────────────────
# Club CSV Helper (Unchanged)
# ────────────────────────────────────────────────────────────────────────────────
def build_club_player_set(csv_source) -> Set[str]:
    # ... (keep existing code) ...
    try:
        # Ensure csv_source is a Path object or string path
        if not isinstance(csv_source, (str, Path)):
             flash(f"Invalid CSV source type: {type(csv_source)}", "danger")
             return set()

        if not Path(csv_source).exists():
            flash(f"Club roster file not found: {csv_source}", "danger")
            return set()

        # Attempt to read CSV, handle potential errors
        try:
            df = pd.read_csv(csv_source, skiprows=3)
        except pd.errors.EmptyDataError:
            flash(f"Club roster file is empty: {Path(csv_source).name}", "warning")
            return set()
        except Exception as read_err:
            flash(f"Error reading club roster {Path(csv_source).name}: {read_err}", "danger")
            return set()

        # Check if required columns exist
        if "Status" not in df.columns or "Person" not in df.columns:
            flash(f"Missing required columns ('Status', 'Person') in {Path(csv_source).name}", "warning")
            return set()

        # Process the DataFrame
        df_filtered = df[df["Status"].astype(str).str.strip().str.upper() == "OK"]
        # Handle potential errors if 'Person' column contains non-string data
        try:
            df_filtered["Full Name"] = df_filtered["Person"].apply(lambda x: " ".join(str(x).strip().lower().split(", ")[::-1]) if isinstance(x, str) and ', ' in x else str(x).strip().lower())
        except Exception as apply_err:
             flash(f"Error processing names in {Path(csv_source).name}: {apply_err}", "warning")
             return set(df_filtered["Person"].astype(str).str.strip().str.lower().tolist()) # Fallback to raw names

        return set(df_filtered["Full Name"].tolist())

    except Exception as e:
        flash(f"Error processing club roster {csv_source}: {e}", "danger")
        return set()


# ────────────────────────────────────────────────────────────────────────────────
# Main Routes
# ────────────────────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    """Main hub: choose Eligibility Checker or League Checklists."""
    return render_template("home.html")

@app.route("/eligibility", methods=["GET", "POST"])
def eligibility():
    """Player Eligibility Checker route."""
    saved_rosters = _load_meta()
    # Sort by club name for display
    sorted_rosters = sorted(saved_rosters.items(), key=lambda item: item[1].get("club_name", "").lower())

    if request.method == "POST":
        player_limit      = request.form.get("player_limit", "5 or fewer")
        max_club_players  = 1 if "5 or fewer" in player_limit else 2
        club_players: Set[str] = set()
        error_occurred = False # Flag to prevent processing if setup fails

        # 1. Process existing saved selections
        selected_roster_ids = request.form.getlist("existing_rosters")
        for rid in selected_roster_ids:
            if rid not in saved_rosters:
                flash(f"Unknown saved roster ID '{rid}' selected.", "warning")
                continue
            roster_filename = saved_rosters[rid].get("filename")
            if not roster_filename:
                 flash(f"Metadata missing filename for roster ID '{rid}'.", "warning")
                 continue
            roster_path = ROSTER_DIR / roster_filename
            club_players.update(build_club_player_set(roster_path)) # build_club_player_set handles file not found

        # 2. Process new CSV uploads
        uploaded_csvs = request.files.getlist("club_csvs")
        club_names_in_form = request.form.getlist("club_names[]") # Names selected/entered for uploaded files
        # Ensure we have a name for each uploaded file
        if len(uploaded_csvs) != len(club_names_in_form):
             flash("Mismatch between uploaded CSV files and club names provided.", "danger")
             error_occurred = True
             # Don't proceed further if this basic check fails

        if not error_occurred:
            for idx, fs in enumerate(uploaded_csvs):
                if not fs or not fs.filename:
                    continue # Skip empty file inputs

                club_name_input = club_names_in_form[idx].strip()
                if not club_name_input:
                     flash(f"Club name missing for uploaded file: {fs.filename}", "warning")
                     # Decide if this is an error or just skip the file
                     continue # Skip this file if name is missing

                # Handle 'Other' - though JS should prevent this if working correctly
                if club_name_input == "Other":
                     flash(f"Please specify a club name for {fs.filename} instead of 'Other'.", "warning")
                     continue # Skip file if 'Other' is selected without text input

                # Save the roster (replaces if name exists)
                club_path = save_or_replace_roster(fs, club_name_input)
                if club_path:
                    club_players.update(build_club_player_set(club_path))
                else:
                    error_occurred = True # Flag error if saving failed

        # 3. Process PDF upload
        im_pdf = request.files.get("im_pdf")
        if not im_pdf or not im_pdf.filename:
            flash("Please upload the IM Team Rosters PDF.", "danger")
            error_occurred = True

        if error_occurred:
             # If any errors occurred during setup, re-render the form
             return render_template("index.html", saved_rosters=saved_rosters, sorted_rosters=sorted_rosters)


        # --- Proceed only if setup was successful ---
        text = (
            extract_text_pdfplumber(im_pdf)
            or extract_text_pymupdf(im_pdf)
            or extract_text_html(im_pdf)
        )
        if not text:
            flash("❌ Failed to extract text from PDF. Please try a different PDF or check the file.", "danger")
            return render_template("index.html", saved_rosters=saved_rosters, sorted_rosters=sorted_rosters)

        # 4. Parse PDF text for teams and players
        teams: Dict[str, List[str]] = {}
        elite_players: Set[str] = set() # Players explicitly on Elite teams
        elite_teams: Set[str] = set()   # Names of Elite teams
        current_team = None
        recording_players = False
        current_level = "Regular" # Assume Regular unless -> Elite is seen

        for line in text.split("\n"):
            line = line.strip()
            if not line: continue # Skip empty lines

            # Skip headers/footers
            if (
                "Oregon State University" in line
                or "imleagues.com" in line
                or re.match(r"\d{1,2}/\d{1,2}/\d{2,4},? \d{1,2}:\d{2}\s*(?:[APap][Mm])?", line) # Improved date/time regex
                or "Page" in line # Common footer element
            ):
                continue

            # Detect level change
            if "->" in line and ("Elite" in line or "Regular" in line):
                current_level = "Elite" if "Elite" in line else "Regular"
                # print(f"Level set to: {current_level}") # Debug
                continue

            # Detect team name (ends with "Rosters")
            # Handle cases like "Team Name Rosters" or "Team Name - Men's A Rosters"
            m = re.match(r"^(.*?)\s*(?:-\s*\w+[']?\w?\s*[AB]?)?\s*Rosters", line, re.IGNORECASE)
            if m:
                current_team = m.group(1).strip()
                if not current_team: continue # Skip if team name is empty

                teams[current_team] = []
                if current_level == "Elite":
                    elite_teams.add(current_team)
                    # print(f"Elite Team Found: {current_team}") # Debug
                # print(f"Team Found: {current_team} (Level: {current_level})") # Debug
                recording_players = False # Reset player recording until header
                continue

            # Detect start of player list for the current team
            # Look for header variations
            if current_team and re.search(r"Name\s+(?:Gender\s+)?Status", line, re.IGNORECASE):
                recording_players = True
                # print(f"Player recording started for {current_team}") # Debug
                continue

            # Record players if in recording mode and line looks like a player entry
            # Basic check: not empty, doesn't look like another team name or header
            if recording_players and current_team:
                 # Attempt to extract name - assumes name is before Male/Female/Status
                 player_name_match = re.match(r"^(.*?)(?:\s+(?:Male|Female|Other)\b.*|\s+OK\b.*|$)", line, re.IGNORECASE)
                 if player_name_match:
                     p = player_name_match.group(1).strip()
                     # Clean player name
                     p = re.sub(r"^[C]-\s*", "", p, flags=re.IGNORECASE) # Remove C- prefix
                     p = re.sub(r"\s*\(Nomad\)$", "", p, flags=re.IGNORECASE) # Remove (Nomad) suffix
                     p = p.strip()

                     if p: # Only add if name is not empty after cleaning
                         p_lower = p.lower()
                         teams[current_team].append(p_lower)
                         if current_team in elite_teams:
                             elite_players.add(p_lower)
                         # print(f"  Player Added: {p_lower} to {current_team}") # Debug
                 # else:
                     # print(f"  Skipped Line (no name match): {line}") # Debug


        # Combine club players and elite players
        all_restricted_players = club_players.union(elite_players)
        # print(f"Total Restricted Players: {len(all_restricted_players)}") # Debug
        # print(f"Restricted List: {all_restricted_players}") # Debug

        # Calculate violations
        violations: Dict[str, int] = {}
        team_club_members: Dict[str, List[str]] = {} # Store display names (Title Case)

        for team, roster in teams.items():
            # Skip Elite teams themselves from violation checks
            if team in elite_teams:
                # print(f"Skipping Elite team {team} from violation check.") # Debug
                continue

            # Find restricted players on this team's roster
            restricted_on_team = [player for player in roster if player in all_restricted_players]
            display_names = sorted([name.title() for name in restricted_on_team]) # Title case for display

            if restricted_on_team:
                 team_club_members[team] = display_names
                 # print(f"Team {team}: Restricted Members: {display_names}") # Debug

            if len(restricted_on_team) > max_club_players:
                violations[team] = len(restricted_on_team)
                # print(f"Violation Found: Team {team} has {len(restricted_on_team)} restricted players (Max: {max_club_players})") # Debug


        # Render results template
        return render_template(
            "results.html",
            max_club_players=max_club_players,
            violations=violations,
            team_club_members=team_club_members,
            # Optional: Pass counts for debugging/display
            # total_teams=len(teams),
            # total_elite_teams=len(elite_teams),
            # total_club_players=len(club_players),
            # total_elite_players=len(elite_players),
            # total_restricted=len(all_restricted_players)
        )

    # GET request: Render the initial form
    return render_template("index.html", saved_rosters=saved_rosters, sorted_rosters=sorted_rosters)


# ────────────────────────────────────────────────────────────────────────────────
# Run Application
# ────────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Make sure database tables are created
    # This is now handled at the end of models.py
    # import models # Ensure models are loaded
    # from db import Base, ENG
    # Base.metadata.create_all(ENG)

    # Consider using environment variables for debug and port
    app.run(debug=True, host="0.0.0.0", port=5000)

