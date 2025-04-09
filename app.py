# app.py
from gevent import monkey
monkey.patch_all()

import time, json
from uuid import uuid4
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
import threading
import tasks  # This module contains our processing code and Redis status functions

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Replace with your secret key

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
                csv_content = club_csv.read().decode("utf-8")
                club_csvs_data.append({"filename": club_csv.filename, "content": csv_content})
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

    # Render the loading page with the task ID.
    return render_template("loading.html", task_id=task_id)

@app.route("/stream/<task_id>")
def stream(task_id):
    def event_stream():
        last_status = None
        while True:
            status_data = tasks.get_status(task_id)
            status = status_data.get("status")
            if status != last_status:
                # Yield the update as a JSON string.
                yield f"data: {json.dumps(status_data)}\n\n"
                last_status = status
            if status in ["SUCCESS", "FAILED"]:
                # Once processing is done, break from the loop.
                break
            time.sleep(2)
    return Response(event_stream(), mimetype="text/event-stream")

@app.route("/result/<task_id>")
def result(task_id):
    status_data = tasks.get_status(task_id)
    if status_data.get("status") == "SUCCESS":
        return render_template("results.html", **status_data.get("result"))
    else:
        flash("The results are not ready yet, please wait.")
        return redirect(url_for("index"))

# Existing /status endpoint can remain for debugging if needed.
@app.route("/status/<task_id>")
def task_status(task_id):
    status_data = tasks.get_status(task_id)
    return jsonify({"state": status_data.get("status"), "result": status_data.get("result")})

if __name__ == "__main__":
    app.run(debug=True)