import os
import re
import time
from io import StringIO, BytesIO
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import pandas as pd
import pdfplumber
import fitz  # PyMuPDF
import pdf2txt
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text_to_fp
from celery import Celery

# --- Flask App Setup ---
app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Replace with a secure secret

# Celery configuration (using Redis as the broker and backend)
app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379/0',  # update as needed
    CELERY_RESULT_BACKEND='redis://localhost:6379/0'
)

def make_celery(app):
    celery = Celery(app.import_name,
                    broker=app.config['CELERY_BROKER_URL'],
                    backend=app.config['CELERY_RESULT_BACKEND'])
    celery.conf.update(app.config)
    
    # Use Flask application context in Celery tasks
    class ContextTask(celery.Task):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return super(ContextTask, self).__call__(*args, **kwargs)
    celery.Task = ContextTask
    return celery

celery = make_celery(app)

# Import the tasks module so that process_task is registered.
import tasks

# --- Web Routes ---

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/process", methods=["POST"])
def process():
    overall_start_time = time.time()
    print("POST received!")
    print("request.files:", request.files)
    print("request.form:", request.form)

    # Retrieve player limit selection
    player_limit = request.form.get("player_limit", "5 or fewer")

    # Process club CSV files (read into memory as text)
    club_csvs_data = []
    club_csvs = request.files.getlist("club_csvs")
    for club_csv in club_csvs:
        if club_csv and club_csv.filename:
            try:
                csv_content = club_csv.read().decode('utf-8')
                club_csvs_data.append({
                    'filename': club_csv.filename,
                    'content': csv_content
                })
            except Exception as e:
                flash(f"Error processing CSV {club_csv.filename}: {e}")

    # Read the IM Team Rosters PDF into memory as bytes
    im_pdf = request.files.get("im_pdf")
    if not im_pdf:
        flash("Please upload a PDF for IM Team Rosters.")
        return redirect(url_for("index"))
    im_pdf_bytes = im_pdf.read()

    # Enqueue the processing task
    task = tasks.process_task.delay(club_csvs_data, im_pdf_bytes, player_limit)
    print(f"Task enqueued with id: {task.id}")
    print(f"[Celery] Overall processing setup took {time.time() - overall_start_time:.2f} seconds")
    # Render a loading page that polls for task status.
    return render_template("loading.html", task_id=task.id)

@app.route("/status/<task_id>")
def task_status(task_id):
    task = tasks.process_task.AsyncResult(task_id)
    if task.state == "PENDING":
        response = {"state": task.state, "status": "Pending..."}
    elif task.state != "FAILURE":
        response = {"state": task.state, "result": task.result}
    else:
        response = {"state": task.state, "status": str(task.info)}
    return jsonify(response)

@app.route("/result/<task_id>")
def result(task_id):
    task = tasks.process_task.AsyncResult(task_id)
    if task.state == "SUCCESS":
        result = task.result
        return render_template("results.html", **result)
    else:
        flash("The results are not ready yet, please wait.")
        return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)