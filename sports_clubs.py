# sports_clubs.py

from flask import (
    Blueprint, render_template, request, flash, redirect, url_for,
    send_file, 
    current_app,
    session # Import session
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
# import pandas as pd # Not directly used in this file after moving processing
from datetime import datetime, date
from io import BytesIO
# from decimal import Decimal # Not directly used
# import openpyxl # Not directly used
# from openpyxl.utils.dataframe import dataframe_to_rows # Not directly used
# from openpyxl.styles import Font, Alignment, Border, Side, PatternFill, NamedStyle, numbers # Not directly used
# from openpyxl.worksheet.dimensions import ColumnDimension, DimensionHolder # Not directly used
# from openpyxl.utils import get_column_letter # Not directly used
import traceback

# Import Flask-WTF for forms
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField
from wtforms.validators import DataRequired


# Import the processing function
from processing_utils import update_summary_file

# Decorator and Models/DB Session
try:
    # Attempt to import from admin.py first as per original logic
    from admin import admin_required
except ImportError:
    # Fallback definition if admin.py or admin_required is not found there
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
from db import SessionLocal # Using SessionLocal as per original
# from sqlalchemy import desc, func, case, cast, String # Not directly used here

# Define allowed extensions for uploads
ALLOWED_EXTENSIONS = {'xlsx'}

# Create the blueprint
sc_bp = Blueprint('sports_clubs', __name__, url_prefix='/admin/sports-clubs', template_folder='templates')

# Define Forms
class FoundationReconciliationForm(FlaskForm):
    drs_report = FileField('DRS FS Report (Excel)', validators=[DataRequired()])
    drs_sheet_name = StringField('DRS Report Sheet Name', validators=[DataRequired()], default='4100-774390') # Example default
    donor_report = FileField('Donor Report (Excel)', validators=[DataRequired()])
    summary_file = FileField('Current Foundation Summary (Excel)', validators=[DataRequired()])
    submit = SubmitField('Process Files')

# class FoundationTransactionReviewForm(FlaskForm): # Define if needed for review page template
#     # Example:
#     # club_id = SelectField('Assign to Club', coerce=int, validators=[DataRequired()])
#     # submit = SubmitField('Assign Club')
#     pass


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@sc_bp.route('/foundation', methods=['GET', 'POST'])
@login_required
@admin_required
def foundation_reconciliation():
    """Handles the upload of reports and the existing summary, processes them,
       saves results, and redirects to show status and next steps."""
    form = FoundationReconciliationForm() # Instantiate the form

    if form.validate_on_submit(): # Replaces request.method == 'POST' and manual file checks for WTForms
        # --- File Upload Handling (WTForms handles file data) ---
        drs_file = form.drs_report.data
        donor_file = form.donor_report.data
        summary_file = form.summary_file.data
        drs_sheet_name = form.drs_sheet_name.data # Get sheet name from form

        # Basic check if files are provided (WTForms validators should handle more)
        if not drs_file or not donor_file or not summary_file:
            flash('Missing file data. Please select all three report files.', 'warning')
            return redirect(request.url)

        # Filename checks (allowed_file can still be useful for extension validation if not covered by WTForms)
        if (allowed_file(drs_file.filename) and
                allowed_file(donor_file.filename) and
                allowed_file(summary_file.filename)):

            upload_folder = current_app.config.get('UPLOAD_FOLDER', os.path.join(current_app.root_path, 'uploads'))
            os.makedirs(upload_folder, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')

            # Secure filenames and create temporary paths
            # Using form field names for clarity, but original filename for secure_filename
            drs_filename_secure = secure_filename(f"drs_{current_user.id}_{timestamp}.xlsx")
            donor_filename_secure = secure_filename(f"donor_{current_user.id}_{timestamp}.xlsx")
            summary_filename_secure = secure_filename(f"summary_{current_user.id}_{timestamp}.xlsx")

            drs_path = os.path.join(upload_folder, drs_filename_secure)
            donor_path = os.path.join(upload_folder, donor_filename_secure)
            summary_path = os.path.join(upload_folder, summary_filename_secure)

            files_saved = False
            try:
                # Save uploaded files temporarily (using .save() method of FileStorage)
                drs_file.save(drs_path)
                donor_file.save(donor_path)
                summary_file.save(summary_path)
                files_saved = True
                flash('Files successfully uploaded. Processing...', 'info')
                current_app.logger.info("Files saved, starting processing via update_summary_file.")


                # --- Call the processing function ---
                # Pass drs_sheet_name to the processing function
                file_buffer, results = update_summary_file(drs_path, donor_path, summary_path, drs_sheet_name_override=drs_sheet_name)
                current_app.logger.info(f"Processing results: {results}")


                # --- Handle Results ---
                session['last_results'] = results # Store the results dict for display after redirect

                if results.get('errors'): # Check if 'errors' key exists and has content
                    for error in results['errors']: 
                        flash(f"Processing Error: {error}", 'danger')
                    current_app.logger.error(f"Processing errors: {results['errors']}")
                    session.pop('last_summary_buffer', None) # Clear buffer on error
                    session.pop('last_summary_timestamp', None) # Clear timestamp on error
                else:
                    if file_buffer:
                        session['last_summary_buffer'] = file_buffer.getvalue()
                        session['last_summary_timestamp'] = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
                        current_app.logger.info(f"Stored summary buffer ({len(session['last_summary_buffer'])} bytes) and timestamp in session.")
                        flash('File processing complete. You can download the updated summary.', 'success')
                    else:
                        session.pop('last_summary_buffer', None) # Clear if no buffer
                        session.pop('last_summary_timestamp', None) # Clear timestamp if no buffer
                        # Check if there were no errors but also no file buffer (e.g. no data to process)
                        if not results.get('warnings'): # Add a generic warning if no specific one exists
                             results['warnings'] = results.get('warnings', []) # Ensure warnings list exists
                             results['warnings'].append("Processing completed, but no update file was generated (e.g., no new data or matching transactions).")
                        current_app.logger.warning("Processing completed but no summary buffer generated.")
                    
                    # Flash warnings if any
                    if results.get('warnings'):
                        for warning in results['warnings']:
                            flash(f"Processing Warning: {warning}", 'warning')


                    # --- Save newly identified transactions to DB (original logic) ---
                    if results.get('new_transactions_for_db'):
                        current_app.logger.info(f"Attempting to save {len(results['new_transactions_for_db'])} transactions to DB...")
                        with SessionLocal() as db_session: # Use 'db_session' to avoid conflict
                            db_session.add_all(results['new_transactions_for_db'])
                            try:
                                db_session.commit()
                                current_app.logger.info("Successfully saved new transactions to DB.")
                                flash(f"{len(results['new_transactions_for_db'])} new transaction(s) saved to history.", "info")
                            except Exception as commit_err:
                                db_session.rollback()
                                err_msg = f"Database commit error for new transactions: {commit_err}"
                                current_app.logger.error(f"[Error] {err_msg}")
                                flash(f"Error saving transaction history: {commit_err}", "danger")
                                # Add to results for display
                                if 'errors' not in results: results['errors'] = []
                                results['errors'].append(f"DB Save Error: {str(commit_err)}")
                                session['last_results'] = results # Update session with error

            except Exception as e:
                flash(f'An error occurred during file upload or processing: {e}', 'danger')
                current_app.logger.error(f"Error during foundation upload/process: {e}", exc_info=True)
                traceback.print_exc()
                session.pop('last_results', None) 
                session.pop('last_summary_buffer', None)
                session.pop('last_summary_timestamp', None)
            finally:
                # --- Clean up temporary files ---
                try:
                    if files_saved:
                        if os.path.exists(drs_path): os.remove(drs_path)
                        if os.path.exists(donor_path): os.remove(donor_path)
                        if os.path.exists(summary_path): os.remove(summary_path)
                        current_app.logger.info("Temporary upload files cleaned up.")
                except OSError as e:
                    current_app.logger.error(f"Error removing temporary upload file: {e}")

            return redirect(url_for('.foundation_reconciliation'))

        else: # If file check failed (should be less likely with WTForms FileAllowed validator if used)
            flash('Invalid file type. Only .xlsx files are allowed.', 'warning') # Simplified message
            # Errors from WTForms validators will be flashed automatically or shown by render_field
            return redirect(request.url) # Redirect to clear POST
    
    # --- GET Request Logic (or if form validation failed on POST) ---
    # Pop results from the previous POST action for one-time display
    last_results_for_template = session.pop('last_results', None) 
    
    # Get current count of items needing review from DB
    needs_review_count_db = 0
    try:
        with SessionLocal() as db_session:
            needs_review_count_db = db_session.query(FoundationTransaction).filter_by(status=FoundationTransaction.STATUS_NEEDS_REVIEW).count()
    except Exception as e:
        current_app.logger.error(f"Error querying needs_review_count: {e}")
        flash("Could not retrieve count of items needing review.", "danger")


    return render_template(
        'sports_clubs/foundation_reconciliation.html',
        form=form, # Pass form for rendering
        processing_results=last_results_for_template, # Pass popped results of last processing attempt
        num_needs_review_db=needs_review_count_db # Pass current DB count for the warning
        # The template will use session.get('last_summary_timestamp') and session.get('last_summary_buffer')
        # to determine if the download button should be shown.
    )

@sc_bp.route('/foundation/download_last')
@login_required
@admin_required
def download_last_summary():
    """Provides the last processed summary file for download."""
    summary_buffer_bytes = session.pop('last_summary_buffer', None) # Pop buffer
    session.pop('last_summary_timestamp', None) # Also pop timestamp to hide button after download

    if summary_buffer_bytes:
        file_buffer = BytesIO(summary_buffer_bytes) # Convert bytes back to BytesIO
        today = date.today()
        # Fiscal year calculation (July 1st is typical start)
        fiscal_year = today.year if today.month < 7 else today.year + 1
        fiscal_year_short = str(fiscal_year)[-2:]
        download_filename = f"FY{fiscal_year_short}_Foundation_Summary_Updated_{today.strftime('%Y%m%d_%H%M%S')}.xlsx" # Added timestamp for uniqueness
        current_app.logger.info(f"Serving download: {download_filename}")
        return send_file(
            file_buffer,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=download_filename
        )
    else:
        flash("No summary file available for download or session expired. Please process files first.", "warning")
        current_app.logger.warning("Download attempt failed: no summary buffer in session.")
        return redirect(url_for('.foundation_reconciliation'))


@sc_bp.route('/foundation/review', methods=['GET', 'POST'])
@login_required
@admin_required
def foundation_review():
    """Displays transactions needing review and handles assignment."""
    # review_form = FoundationTransactionReviewForm() # Instantiate if defined and used in template

    if request.method == 'POST':
        transaction_id = request.form.get('transaction_id')
        club_id = request.form.get('club_id')

        if not transaction_id or not club_id: # Basic validation
            flash('Missing transaction ID or club ID.', 'danger')
            return redirect(url_for('.foundation_review'))

        try:
            # Ensure IDs are integers
            transaction_id = int(transaction_id)
            club_id = int(club_id)

            with SessionLocal() as db_session: # Use 'db_session'
                transaction = db_session.query(FoundationTransaction).filter_by(id=transaction_id, status=FoundationTransaction.STATUS_NEEDS_REVIEW).first()
                club = db_session.query(Club).filter_by(id=club_id).first()

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
                    # transaction.reviewed_by_user_id = current_user.id # Optional: track who reviewed
                    db_session.commit()
                    flash(f'Transaction {transaction.journal_ref or transaction.drs_description or transaction.id} successfully assigned to {club.name}.', 'success')
                    current_app.logger.info(f"Transaction ID {transaction_id} assigned to Club ID {club_id} by User ID {current_user.id}")

        except ValueError:
             flash('Invalid transaction or club ID format.', 'danger')
        except Exception as e:
            # db_session.rollback() # Rollback is implicitly handled by context manager on exception if not committed
            flash(f'An error occurred while assigning the club: {e}', 'danger')
            current_app.logger.error(f"Error assigning club for TX_ID {transaction_id}: {e}", exc_info=True)
            traceback.print_exc()

        return redirect(url_for('.foundation_review')) 

    # --- GET Request Logic ---
    transactions_to_review = []
    active_clubs = []
    try:
        with SessionLocal() as db_session: # Use 'db_session'
            transactions_to_review = db_session.query(FoundationTransaction).filter(
                FoundationTransaction.status == FoundationTransaction.STATUS_NEEDS_REVIEW
            ).order_by(FoundationTransaction.transaction_date.asc()).all() # Added .asc()

            active_clubs = db_session.query(Club).filter_by(is_active=True).order_by(Club.name).all()
    except Exception as e:
        current_app.logger.error(f"Error querying data for review page: {e}")
        flash("Could not retrieve data for the review page.", "danger")


    return render_template(
        'sports_clubs/foundation_review.html',
        transactions=transactions_to_review,
        clubs=active_clubs
        # form=review_form # Pass if using a WTForm on the review page
    )
