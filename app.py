# app.py
import time
from uuid import uuid4
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from tasks import process_long_task

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Replace with your real secret key

# Global dictionary to track tasks.
tasks_status = {}

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/process", methods=["POST"])
def process():
    # Retrieve form inputs.
    player_limit = request.form.get("player_limit", "5 or fewer")

    # Process uploaded club CSVs.
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

    # Read the IM Team Rosters PDF.
    im_pdf = request.files.get("im_pdf")
    if not im_pdf:
        flash("Please upload a PDF for IM Team Rosters.")
        return redirect(url_for("index"))
    im_pdf_bytes = im_pdf.read()

    # Generate a unique task ID and set initial status.
    task_id = str(uuid4())
    tasks_status[task_id] = {"status": "PENDING", "result": None}
    
    # Start the background thread to process the task.
    import threading
    thread = threading.Thread(
        target=process_long_task, 
        args=(club_csvs_data, im_pdf_bytes, player_limit, task_id, tasks_status)
    )
    thread.start()
    
    # Render a loading page that polls for task status.
    return render_template("loading.html", task_id=task_id)

@app.route("/status/<task_id>")
def task_status(task_id):
    status = tasks_status.get(task_id)
    if not status:
        return jsonify({"state": "NOT_FOUND"})
    return jsonify({"state": status["status"], "result": status["result"]})

@app.route("/result/<task_id>")
def result(task_id):
    status = tasks_status.get(task_id)
    if status and status["status"] == "SUCCESS":
        result = status["result"]
        return render_template("results.html", **result)
    else:
        flash("The results are not ready yet, please wait.")
        return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)