import os
import re
import tempfile
from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import pdfplumber
import fitz  # PyMuPDF
import pdf2txt
from bs4 import BeautifulSoup

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Replace with a secure secret key

def extract_text_pdfplumber(file_obj):
    try:
        file_obj.seek(0)
        with pdfplumber.open(file_obj) as pdf:
            text = "\n".join([page.extract_text() or "" for page in pdf.pages])
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
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file_obj.read())
            tmp_path = tmp.name
        output_html = tmp_path + ".html"
        pdf2txt.main(["-o", output_html, tmp_path])
        with open(output_html, "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file, "html.parser")
            text = soup.get_text()
        os.remove(output_html)
        os.remove(tmp_path)
        return text
    except Exception as e:
        flash(f"⚠️ HTML extraction failed: {e}")
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Get the player limit selection
        player_limit = request.form.get("player_limit", "5 or fewer")
        max_club_players = 1 if "5 or fewer" in player_limit else 2

        # Get uploaded files
        club_csvs = request.files.getlist("club_csvs")
        im_pdf = request.files.get("im_pdf")
        if not im_pdf:
            flash("Please upload a PDF for IM Team Rosters.")
            return redirect(request.url)

        club_players = set()
        # Process club roster CSVs if any
        for club_csv in club_csvs:
            if club_csv and club_csv.filename:
                try:
                    # Assuming the CSV has a header and data starts after 3 rows
                    club_df = pd.read_csv(club_csv, skiprows=3)
                    # Only include rows where Status equals 'OK' (ignoring case/whitespace)
                    club_df = club_df[club_df['Status'].str.strip().str.upper() == 'OK']
                    club_df['Full Name'] = club_df['Person'].apply(
                        lambda x: ' '.join(x.strip().lower().split(', ')[::-1])
                    )
                    club_players.update(club_df['Full Name'])
                except Exception as e:
                    flash(f"Error processing CSV {club_csv.filename}: {e}")

        # Try extracting text from the PDF using three methods
        text = extract_text_pdfplumber(im_pdf)
        if text is None:
            flash("pdfplumber failed, trying PyMuPDF...")
            im_pdf.seek(0)
            text = extract_text_pymupdf(im_pdf)
        if text is None:
            flash("PyMuPDF failed, trying HTML extraction...")
            im_pdf.seek(0)
            text = extract_text_html(im_pdf)

        if not text:
            flash("❌ Text extraction failed for all methods.")
            return redirect(request.url)

        # Process the extracted text to parse teams and players
        teams = {}
        elite_players = set()
        elite_teams = {}

        lines = text.split("\n")
        current_team = None
        recording_players = False
        current_level = "Regular"

        for line in lines:
            # Skip header/footer lines or date stamps
            if ("Oregon State University" in line or "imleagues.com" in line or
                re.match(r'\d{1,2}/\d{1,2}/\d{2}, \d{1,2}:\d{2} [APap][Mm]', line)):
                continue
            if "->" in line:
                current_level = "Elite" if "Elite" in line else "Regular"
                continue
            match = re.match(r"(.+?)Rosters", line)
            if match:
                current_team = match.group(1).strip()
                teams[current_team] = []
                if current_level == "Elite":
                    elite_teams[current_team] = "Elite"
                recording_players = False
                continue
            if "Name Gender Status" in line:
                recording_players = True
                continue
            if recording_players and line.strip():
                player_name = line.split(" Male ")[0].split(" Female ")[0].strip()
                player_name = re.sub(r"^C-", "", player_name, flags=re.IGNORECASE)
                player_name = re.sub(r"\(Nomad\)$", "", player_name, flags=re.IGNORECASE)
                player_name = player_name.lower()
                if current_team in elite_teams:
                    elite_players.add(player_name)
                if current_team:
                    teams[current_team].append(player_name)

        # Update club players with elite players if any
        club_players.update(elite_players)
        violations = {}
        team_club_members = {}

        for team, roster in teams.items():
            # Skip elite teams from violation check
            if team in elite_teams:
                continue  
            club_on_team = [player.title() for player in roster if player in club_players]
            team_club_members[team] = club_on_team
            if len(club_on_team) > max_club_players:
                violations[team] = len(club_on_team)

        return render_template("results.html",
                               max_club_players=max_club_players,
                               violations=violations,
                               team_club_members=team_club_members)
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)