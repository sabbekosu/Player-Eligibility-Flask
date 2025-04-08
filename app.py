# app.py
import time
from uuid import uuid4
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import threading
import tasks  # Import the tasks module (which includes update_status and get_status)

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Replace with a secure secret key

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/process", methods=["POST"])
def process():
    # Get form inputs.
    player_limit = request.form.get("player_limit", "5 or fewer")

    # Process uploaded CSV files.
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

    # Read the PDF.
    im_pdf = request.files.get("im_pdf")
    if not im_pdf:
        flash("Please upload a PDF for IM Team Rosters.")
        return redirect(url_for("index"))
    im_pdf_bytes = im_pdf.read()

    # Generate a unique task ID.
    task_id = str(uuid4())
    tasks.update_status(task_id, "PENDING")

    # Start the long processing in a background thread.
    thread = threading.Thread(
        target=tasks.process_long_task, 
        args=(club_csvs_data, im_pdf_bytes, player_limit, task_id)
    )
    thread.start()

    # Render a loading page that polls for task status.
    return render_template("loading.html", task_id=task_id)

@app.route("/status/<task_id>")
def task_status(task_id):
    status = tasks.get_status(task_id)
    return jsonify({"state": status.get("status"), "result": status.get("result")})

@app.route("/result/<task_id>")
def result(task_id):
    status = tasks.get_status(task_id)
    if status.get("status") == "SUCCESS":
        return render_template("results.html", **status.get("result"))
    else:
        flash("The results are not ready yet, please wait.")
        return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)