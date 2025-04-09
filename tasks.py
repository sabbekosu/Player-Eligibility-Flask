# tasks.py
import os
import redis
import json
import re
import time
from io import StringIO, BytesIO
import pandas as pd
import pdfplumber
import fitz  # PyMuPDF
import pdf2txt
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text_to_fp

# Read Upstash credentials from environment variables.
UPSTASH_HOST = os.environ.get("UPSTASH_HOST")
UPSTASH_PORT = int(os.environ.get("UPSTASH_PORT", 6379))
UPSTASH_PASSWORD = os.environ.get("UPSTASH_PASSWORD")

if not UPSTASH_HOST or not UPSTASH_PASSWORD:
    raise Exception("UPSTASH_HOST and UPSTASH_PASSWORD environment variables are required")

# Initialize the Redis client with explicit parameters and SSL enabled.
redis_client = redis.Redis(
    host=UPSTASH_HOST,
    port=UPSTASH_PORT,
    password=UPSTASH_PASSWORD,
    ssl=True
)

def update_status(task_id, status, result=None):
    """
    Save the task status and result in Redis.
    """
    data = {"status": status, "result": result}
    redis_client.set(task_id, json.dumps(data), ex=86400)

def get_status(task_id):
    """
    Retrieve the task status and result from Redis.
    """
    data = redis_client.get(task_id)
    if data:
        return json.loads(data)
    else:
        return {"status": "NOT_FOUND", "result": None}

def extract_text_pdfplumber(file_obj):
    try:
        file_obj.seek(0)
        with pdfplumber.open(file_obj) as pdf:
            text = "\n".join([page.extract_text() or "" for page in pdf.pages])
            if text.strip():
                return text
    except Exception as e:
        print(f"pdfplumber error: {e}")
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
        print(f"PyMuPDF error: {e}")
    return None

def extract_text_html(file_obj):
    try:
        file_obj.seek(0)
        output = StringIO()
        # Use pdfminer to produce HTML output and then extract text.
        extract_text_to_fp(file_obj, output, output_type='html')
        html_content = output.getvalue()
        output.close()
        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text()
        if text.strip():
            return text
    except Exception as e:
        print(f"HTML extraction error: {e}")
    return None

def smart_extract_text(file_obj):
    """
    Attempts extraction with pdfplumber first, then PyMuPDF, and lastly HTML extraction.
    """
    try:
        file_obj.seek(0)
        file_bytes = file_obj.read()
        pdf_file = BytesIO(file_bytes)
        text = extract_text_pdfplumber(pdf_file)
        if text is None:
            pdf_file = BytesIO(file_bytes)
            text = extract_text_pymupdf(pdf_file)
        if text is None:
            html_file = BytesIO(file_bytes)
            text = extract_text_html(html_file)
        return text
    except Exception as e:
        print(f"smart_extract_text error: {e}")
        return None

def process_long_task(club_csvs_data, im_pdf_bytes, player_limit, task_id):
    """
    Process the provided CSV and PDF data, then update the task status in Redis.
    """
    # Mark task as processing.
    update_status(task_id, "PROCESSING")
    
    # Build a set of club players from the CSV files.
    club_players = set()
    for csv_item in club_csvs_data:
        try:
            csv_io = StringIO(csv_item['content'])
            club_df = pd.read_csv(csv_io, skiprows=3)
            club_df = club_df[club_df['Status'].str.strip().str.upper() == 'OK']
            club_df['Full Name'] = club_df['Person'].apply(
                lambda x: ' '.join(x.strip().lower().split(', ')[::-1])
            )
            club_players.update(club_df['Full Name'])
        except Exception as e:
            print(f"Error processing CSV {csv_item['filename']}: {e}")

    # Extract text from the PDF.
    im_pdf_file = BytesIO(im_pdf_bytes)
    extraction_start_time = time.time()
    text = smart_extract_text(im_pdf_file)
    extraction_end_time = time.time()
    print(f"[Thread] Extraction took {extraction_end_time - extraction_start_time:.2f} seconds")
    
    if not text:
        update_status(task_id, "FAILED", {"error": "Text extraction failed."})
        return

    # Process the extracted text: parse teams and players.
    teams = {}
    elite_players = set()
    elite_teams = {}
    lines = text.split("\n")
    current_team = None
    recording_players = False
    current_level = "Regular"

    for line in lines:
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

    club_players.update(elite_players)
    violations = {}
    team_club_members = {}
    name_cache = {}

    def convert_title(name):
        if name in name_cache:
            return name_cache[name]
        title_name = name.title()
        name_cache[name] = title_name
        return title_name

    for team, roster in teams.items():
        if team in elite_teams:
            continue
        common_names = club_players.intersection(roster)
        club_on_team = [convert_title(player) for player in roster if player in common_names]
        team_club_members[team] = club_on_team
        max_club_players = 1 if "5 or fewer" in player_limit else 2
        if len(club_on_team) > max_club_players:
            violations[team] = len(club_on_team)
            
    result = {
        "violations": violations,
        "team_club_members": team_club_members,
        "max_club_players": 1 if "5 or fewer" in player_limit else 2
    }
    
    update_status(task_id, "SUCCESS", result)