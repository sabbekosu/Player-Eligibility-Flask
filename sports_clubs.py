# sports_clubs.py

from flask import (
    Blueprint, render_template, request, flash, redirect, url_for,
    send_file, # Still needed for direct download if we keep that option
    current_app,
    session # Import session
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import pandas as pd
from datetime import datetime, date
from io import BytesIO
from decimal import Decimal
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill, NamedStyle, numbers
from openpyxl.worksheet.dimensions import ColumnDimension, DimensionHolder
from openpyxl.utils import get_column_letter
import traceback

# Import the processing function
from processing_utils import update_summary_file

# Decorator and Models/DB Session
try:
    from admin import admin_required
except ImportError:
    from functools import wraps
    def admin_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Ensure user is authenticated and has the 'admin' role
            if not current_user.is_authenticated or getattr(current_user, 'role', None) != 'admin':
                flash('Admin access required.', 'danger')
                return redirect(url_for('auth.login')) # Redirect to login if not admin
            return f(*args, **kwargs)
        return decorated_function

from models import FoundationTransaction, Club # Import Club model
from db import SessionLocal
from sqlalchemy import desc, func, case, cast, String

# Define allowed extensions for uploads
ALLOWED_EXTENSIONS = {'xlsx'}

# Create the blueprint
sc_bp = Blueprint('sports_clubs', __name__, url_prefix='/admin/sports-clubs', template_folder='templates')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@sc_bp.route('/foundation', methods=['GET', 'POST'])
@login_required
@admin_required
def foundation_reconciliation():
    """Handles the upload of reports and the existing summary, processes them,
       saves results, and redirects to show status and next steps."""

    if request.method == 'POST':
        # --- File Upload Handling ---
        required_files = ['drs_report', 'donor_report', 'summary_file']
        if not all(f in request.files for f in required_files):
            flash('Missing file part in upload request. Please upload all three files.', 'danger')
            return redirect(request.url)

        drs_file = request.files['drs_report']
        donor_file = request.files['donor_report']
        summary_file = request.files['summary_file']

        if drs_file.filename == '' or donor_file.filename == '' or summary_file.filename == '':
            flash('No selected file for one or more inputs. Please select all three report files.', 'warning')
            return redirect(request.url)

        if (drs_file and allowed_file(drs_file.filename) and
                donor_file and allowed_file(donor_file.filename) and
                summary_file and allowed_file(summary_file.filename)):

            upload_folder = current_app.config.get('UPLOAD_FOLDER', os.path.join(current_app.root_path, 'uploads'))
            os.makedirs(upload_folder, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')

            # Secure filenames and create temporary paths
            drs_filename = secure_filename(f"drs_{current_user.id}_{timestamp}.xlsx")
            donor_filename = secure_filename(f"donor_{current_user.id}_{timestamp}.xlsx")
            summary_filename_orig = secure_filename(summary_file.filename)
            summary_filename_temp = secure_filename(f"summary_{current_user.id}_{timestamp}.xlsx")

            drs_path = os.path.join(upload_folder, drs_filename)
            donor_path = os.path.join(upload_folder, donor_filename)
            summary_path = os.path.join(upload_folder, summary_filename_temp)

            files_saved = False
            try:
                # Save uploaded files temporarily
                drs_file.save(drs_path)
                donor_file.save(donor_path)
                summary_file.save(summary_path)
                files_saved = True
                flash('Files successfully uploaded. Processing...', 'info')

                # --- Call the processing function ---
                file_buffer, results = update_summary_file(drs_path, donor_path, summary_path)

                # --- Handle Results ---
                if results['errors']:
                    for error in results['errors']: flash(f"Processing Error: {error}", 'danger')
                    session.pop('processing_complete', None) # Clear flags if error
                    session.pop('last_results', None)
                    session.pop('last_summary_buffer', None)
                else:
                    # --- Save newly identified transactions to DB ---
                    if results.get('new_transactions_for_db'):
                        print(f"Attempting to save {len(results['new_transactions_for_db'])} transactions to DB...")
                        with SessionLocal() as db:
                            db.add_all(results['new_transactions_for_db'])
                            try:
                                db.commit()
                                print("Successfully saved new transactions to DB.")
                            except Exception as commit_err:
                                db.rollback()
                                err_msg = f"Database commit error for new transactions: {commit_err}"
                                print(f"[Error] {err_msg}")
                                flash(f"Error saving transaction history: {commit_err}", "danger")
                                # Still mark processing as complete, but warn user

                    # --- Store results and file buffer in session ---
                    session['processing_complete'] = True
                    session['last_results'] = results # Store the results dict
                    # Store the file buffer (convert BytesIO to bytes)
                    if file_buffer:
                        session['last_summary_buffer'] = file_buffer.getvalue()
                        print(f"Stored summary buffer in session ({len(session['last_summary_buffer'])} bytes).")
                    else:
                        session.pop('last_summary_buffer', None) # Clear if no buffer
                        flash("Processing completed, but could not generate the updated file for download.", "warning")

            except Exception as e:
                flash(f'An error occurred during file upload or processing: {e}', 'danger')
                print(f"Error during foundation upload/process: {e}")
                traceback.print_exc()
                session.pop('processing_complete', None) # Clear flags on error
                session.pop('last_results', None)
                session.pop('last_summary_buffer', None)
            finally:
                # --- Clean up temporary files ---
                try:
                    if files_saved:
                        if os.path.exists(drs_path): os.remove(drs_path)
                        if os.path.exists(donor_path): os.remove(donor_path)
                        if os.path.exists(summary_path): os.remove(summary_path)
                except OSError as e:
                    print(f"Error removing temporary upload file: {e}")

            # --- Redirect back to the GET page to show results/buttons ---
            return redirect(url_for('.foundation_reconciliation'))

        else: # If file check failed
            flash('Invalid file type or missing file. Only .xlsx files are allowed for all three inputs.', 'warning')
            return redirect(request.url)

    # --- GET Request Logic ---
    processing_complete = session.pop('processing_complete', False) # Get and remove flag
    last_results = session.pop('last_results', None) # Get and remove results
    summary_buffer_bytes = session.pop('last_summary_buffer', None) # Get and remove buffer bytes

    # Store buffer bytes temporarily for download link if present
    # This is a simple approach; a more robust solution might use a temp file store
    # or a dedicated cache if buffers are large or persistence is needed across restarts.
    download_available = False
    if summary_buffer_bytes:
        # Store in session again under a persistent key for the download route
        session['download_buffer'] = summary_buffer_bytes
        download_available = True

    # Always get the current count from DB for display
    needs_review_count_db = 0
    with SessionLocal() as db:
        needs_review_count_db = db.query(FoundationTransaction).filter_by(status=FoundationTransaction.STATUS_NEEDS_REVIEW).count()

    return render_template(
        'sports_clubs/foundation_reconciliation.html',
        processing_complete=processing_complete,
        last_results=last_results,
        download_available=download_available, # Pass flag for download button
        needs_review_count=needs_review_count_db # Pass current DB count
    )

# --- NEW Route for Downloading the Last Processed File ---
@sc_bp.route('/foundation/download_last')
@login_required
@admin_required
def download_last_summary():
    """Provides the last processed summary file for download."""
    summary_buffer_bytes = session.pop('download_buffer', None) # Get and remove buffer
    if summary_buffer_bytes:
        file_buffer = BytesIO(summary_buffer_bytes) # Convert bytes back to BytesIO
        today = date.today()
        fiscal_year = today.year + 1 if today.month >= 7 else today.year
        fiscal_year_short = str(fiscal_year)[-2:]
        download_filename = f"FY{fiscal_year_short}_Foundation_Summary_Updated_{today.strftime('%Y%m%d')}.xlsx"
        print(f"Serving download: {download_filename}")
        return send_file(
            file_buffer,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=download_filename
        )
    else:
        flash("No summary file available for download. Please process files first.", "warning")
        return redirect(url_for('.foundation_reconciliation'))


# --- NEW Route for Reviewing Transactions ---
@sc_bp.route('/foundation/review', methods=['GET', 'POST'])
@login_required
@admin_required
def foundation_review():
    """Displays transactions needing review and handles assignment."""
    if request.method == 'POST':
        transaction_id = request.form.get('transaction_id')
        club_id = request.form.get('club_id')

        if not transaction_id or not club_id:
            flash('Missing transaction ID or club ID.', 'danger')
            return redirect(url_for('.foundation_review'))

        try:
            with SessionLocal() as db:
                transaction = db.query(FoundationTransaction).filter_by(id=int(transaction_id), status=FoundationTransaction.STATUS_NEEDS_REVIEW).first()
                club = db.query(Club).filter_by(id=int(club_id)).first()

                if not transaction:
                    flash('Transaction not found or already reviewed.', 'warning')
                elif not club:
                    flash('Selected club not found.', 'danger')
                else:
                    # Update transaction
                    transaction.club_id = club.id
                    transaction.assigned_club_name = club.name
                    transaction.status = FoundationTransaction.STATUS_RECONCILED
                    transaction.updated_at = datetime.utcnow()
                    db.commit()
                    flash(f'Transaction {transaction.journal_ref} successfully assigned to {club.name}.', 'success')

        except ValueError:
             flash('Invalid transaction or club ID.', 'danger')
        except Exception as e:
            db.rollback() # Rollback on error
            flash(f'An error occurred while assigning the club: {e}', 'danger')
            print(f"Error assigning club: {e}")
            traceback.print_exc()

        return redirect(url_for('.foundation_review')) # Redirect back to review page

    # --- GET Request Logic ---
    with SessionLocal() as db:
        transactions_to_review = db.query(FoundationTransaction).filter(
            FoundationTransaction.status == FoundationTransaction.STATUS_NEEDS_REVIEW
        ).order_by(FoundationTransaction.transaction_date).all()

        active_clubs = db.query(Club).filter_by(is_active=True).order_by(Club.name).all()

    return render_template(
        'sports_clubs/foundation_review.html',
        transactions=transactions_to_review,
        clubs=active_clubs
    )
