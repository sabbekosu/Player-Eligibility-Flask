# sports_clubs.py

from flask import (
    Blueprint, render_template, request, flash, redirect, url_for,
    send_file, 
    current_app,
    session 
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime, date
from io import BytesIO
import traceback
import uuid # For generating unique filenames

# Import Flask-WTF for forms
from flask_wtf import FlaskForm
from wtforms import SubmitField, FileField 
from wtforms.validators import DataRequired

from processing_utils import update_summary_file

try:
    from admin import admin_required
except ImportError:
    from functools import wraps
    def admin_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or getattr(current_user, 'role', None) != 'admin':
                flash('Admin access required.', 'danger')
                return redirect(url_for('auth.login')) 
            return f(*args, **kwargs)
        return decorated_function

from models import FoundationTransaction, Club 
from db import SessionLocal 

ALLOWED_EXTENSIONS = {'xlsx'}

sc_bp = Blueprint('sports_clubs', __name__, url_prefix='/admin/sports-clubs', template_folder='templates')

# --- Helper function for Temporary File Storage Path ---
def get_temp_file_storage_path():
    """
    Returns the path for temporary file storage and ensures the directory exists.
    Must be called within an application context.
    """
    # It's good practice to have this configurable, e.g., via app.config
    # For now, using a subdirectory in the instance folder or a dedicated temp folder
    path = os.path.join(current_app.instance_path, 'temp_files') # Using instance_path is safer
    if not os.path.exists(path):
        try:
            os.makedirs(path)
            current_app.logger.info(f"Created temporary file directory: {path}")
        except OSError as e:
            current_app.logger.error(f"Could not create temp_files directory: {path}. Error: {e}")
            return None # Indicate failure
    return path

class FoundationReconciliationForm(FlaskForm):
    drs_report = FileField('DRS FS Report (Excel)', validators=[DataRequired()])
    donor_report = FileField('Donor Report (Excel)', validators=[DataRequired()])
    summary_file = FileField('Current Foundation Summary (Excel)', validators=[DataRequired()])
    submit = SubmitField('Process Files')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@sc_bp.route('/foundation', methods=['GET', 'POST'])
@login_required
@admin_required
def foundation_reconciliation():
    form = FoundationReconciliationForm() 
    temp_file_storage_path = get_temp_file_storage_path() 

    if form.validate_on_submit(): 
        # This is a new processing cycle, clear any old temp file info from session
        session.pop('last_summary_temp_filename', None)
        session.pop('last_summary_timestamp', None)
        session.pop('last_results', None) # Also clear previous results

        drs_file = form.drs_report.data
        donor_file = form.donor_report.data
        summary_file = form.summary_file.data

        if not drs_file or not donor_file or not summary_file:
            flash('Missing file data. Please select all three report files.', 'warning')
            return redirect(request.url)

        if (allowed_file(drs_file.filename) and
                allowed_file(donor_file.filename) and
                allowed_file(summary_file.filename)):

            # Using instance_path for uploads as well, or a dedicated configured UPLOAD_FOLDER
            upload_folder = os.path.join(current_app.instance_path, 'uploads') 
            os.makedirs(upload_folder, exist_ok=True)
            timestamp_files = datetime.now().strftime('%Y%m%d%H%M%S%f')

            drs_filename_secure = secure_filename(f"drs_{current_user.id}_{timestamp_files}.xlsx")
            donor_filename_secure = secure_filename(f"donor_{current_user.id}_{timestamp_files}.xlsx")
            summary_filename_secure = secure_filename(f"summary_{current_user.id}_{timestamp_files}.xlsx")

            drs_path = os.path.join(upload_folder, drs_filename_secure)
            donor_path = os.path.join(upload_folder, donor_filename_secure)
            summary_path = os.path.join(upload_folder, summary_filename_secure)

            files_saved = False
            try:
                drs_file.save(drs_path)
                donor_file.save(donor_path)
                summary_file.save(summary_path)
                files_saved = True
                flash('Files successfully uploaded. Processing...', 'info')
                current_app.logger.info("Files saved, starting processing via update_summary_file.")

                file_buffer, results = update_summary_file(drs_path, donor_path, summary_path) 
                current_app.logger.info(f"Processing results from update_summary_file: {results}")
                session['last_results'] = results # Store results for display on GET

                if results.get('errors'): 
                    for error in results['errors']: 
                        flash(f"Processing Error: {error}", 'danger')
                    current_app.logger.error(f"Processing errors reported by update_summary_file: {results['errors']}")
                else: # No errors reported by processing_utils
                    if file_buffer and temp_file_storage_path: 
                        temp_filename = f"summary_output_{uuid.uuid4().hex}.xlsx"
                        temp_filepath = os.path.join(temp_file_storage_path, temp_filename)
                        try:
                            with open(temp_filepath, 'wb') as f_temp:
                                f_temp.write(file_buffer.getvalue())
                            
                            # Set session variables for the newly processed file
                            session['last_summary_temp_filename'] = temp_filename 
                            session['last_summary_timestamp'] = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
                            current_app.logger.info(f"Stored updated summary in temporary file: {temp_filepath}")
                            flash('File processing complete. You can download the updated summary.', 'success')
                        except IOError as e:
                            current_app.logger.error(f"Could not write temporary summary file: {temp_filepath}. Error: {e}")
                            flash("Error saving processed file. Download may not be available.", "danger")
                            if 'errors' not in results: results['errors'] = [] # Ensure errors list exists
                            results['errors'].append("Server error: Could not save processed file.")
                            session['last_results'] = results # Update results with this new error
                    elif not file_buffer:
                        if not results.get('warnings'): 
                             results['warnings'] = results.get('warnings', []) 
                        results['warnings'].append("Processing completed, but no update file was generated (e.g., no new data or matching transactions).")
                        current_app.logger.warning("Processing completed but no summary buffer generated by update_summary_file.")
                    elif not temp_file_storage_path: 
                        flash("Server configuration error: Temporary file storage not available. Download disabled.", "danger")
                        current_app.logger.error("Temporary file storage path (temp_files) could not be accessed/created.")
                    
                    if results.get('warnings'): # Display warnings if any
                        for warning in results['warnings']:
                            flash(f"Processing Warning: {warning}", 'warning')

                    # Database operations for new transactions
                    if results.get('new_transactions_for_db'):
                        current_app.logger.info(f"Attempting to save {len(results['new_transactions_for_db'])} transactions to DB...")
                        with SessionLocal() as db_session: 
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
                                if 'errors' not in results: results['errors'] = []
                                results['errors'].append(f"DB Save Error: {str(commit_err)}")
                                session['last_results'] = results 

            except Exception as e:
                flash(f'An error occurred during file upload or processing: {e}', 'danger')
                current_app.logger.error(f"Error during foundation upload/process: {e}", exc_info=True)
                traceback.print_exc()
                # session.pop('last_results', None) # Already cleared at the start of POST
            finally:
                # Clean up temporary UPLOADED files (not the generated summary)
                try:
                    if files_saved:
                        if os.path.exists(drs_path): os.remove(drs_path)
                        if os.path.exists(donor_path): os.remove(donor_path)
                        if os.path.exists(summary_path): os.remove(summary_path)
                        current_app.logger.info("Temporary uploaded (input) files cleaned up.")
                except OSError as e:
                    current_app.logger.error(f"Error removing temporary uploaded (input) file: {e}")

            return redirect(url_for('.foundation_reconciliation'))
        else: 
            flash('Invalid file type. Only .xlsx files are allowed.', 'warning') 
            return redirect(request.url) 
    
    # GET request: Retrieve results from session if they were set by a POST
    last_results_for_template = session.get('last_results', None) # Use .get() here, don't pop yet if we want it to persist across simple reloads
                                                                # However, for "one-time" display of POST results, pop is fine.
                                                                # Let's stick with pop for now for "Last Processing Attempt Details"
    if request.method == 'GET': # Only pop for display on initial GET after redirect
        last_results_for_template = session.pop('last_results', None)


    needs_review_count_db = 0
    try:
        with SessionLocal() as db_session:
            needs_review_count_db = db_session.query(FoundationTransaction).filter_by(status=FoundationTransaction.STATUS_NEEDS_REVIEW).count()
    except Exception as e:
        current_app.logger.error(f"Error querying needs_review_count: {e}")
        flash("Could not retrieve count of items needing review.", "danger")

    # The download button visibility in the template relies on:
    # session.get('last_summary_temp_filename') and session.get('last_summary_timestamp')
    # These are NOT popped here, so they persist for the download button.
    return render_template(
        'sports_clubs/foundation_reconciliation.html',
        form=form, 
        processing_results=last_results_for_template, 
        num_needs_review_db=needs_review_count_db 
    )

@sc_bp.route('/foundation/download_last')
@login_required
@admin_required
def download_last_summary():
    # Get the filename from session, DO NOT POP IT.
    temp_filename = session.get('last_summary_temp_filename') 
    # The timestamp is primarily for display; its presence in session is tied to temp_filename.
    # No need to pop 'last_summary_timestamp' here if we want the button to persist.
    
    temp_file_storage_path = get_temp_file_storage_path() 

    if temp_filename and temp_file_storage_path:
        temp_filepath = os.path.join(temp_file_storage_path, temp_filename)
        if os.path.exists(temp_filepath):
            try:
                today = date.today()
                fiscal_year = today.year if today.month < 7 else today.year + 1 # Assuming July 1st fiscal year start
                fiscal_year_short = str(fiscal_year)[-2:]
                download_filename = f"FY{fiscal_year_short}_Foundation_Summary_Updated_{today.strftime('%Y%m%d_%H%M%S')}.xlsx" 
                current_app.logger.info(f"Serving download: {download_filename} from {temp_filepath}")
                
                # Note: The temporary file is NOT deleted after download in this version
                # to allow multiple downloads of the same processed file until a new upload.
                # A separate cleanup mechanism for old files in temp_files would be needed.
                return send_file(
                    temp_filepath,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    as_attachment=True,
                    download_name=download_filename
                )
            except Exception as e:
                current_app.logger.error(f"Error sending file {temp_filepath}: {e}")
                flash("Error occurred while preparing file for download.", "danger")
        else:
            flash("Processed file not found. It might have been cleaned up or an error occurred.", "warning")
            current_app.logger.warning(f"Download attempt failed: temporary file {temp_filepath} not found.")
    else:
        flash("No summary file available for download or session expired. Please process files first.", "warning")
        if not temp_filename:
            current_app.logger.warning("Download attempt failed: no temporary filename in session.")
        if not temp_file_storage_path:
             current_app.logger.warning("Download attempt failed: temporary file storage path not available.")
    
    return redirect(url_for('.foundation_reconciliation'))

@sc_bp.route('/foundation/review', methods=['GET', 'POST'])
@login_required
@admin_required
def foundation_review():
    if request.method == 'POST':
        transaction_id = request.form.get('transaction_id')
        club_id = request.form.get('club_id')

        if not transaction_id or not club_id: 
            flash('Missing transaction ID or club ID.', 'danger')
            return redirect(url_for('.foundation_review'))

        try:
            transaction_id = int(transaction_id)
            club_id = int(club_id)

            with SessionLocal() as db_session: 
                transaction = db_session.query(FoundationTransaction).filter_by(id=transaction_id, status=FoundationTransaction.STATUS_NEEDS_REVIEW).first()
                club = db_session.query(Club).filter_by(id=club_id).first()

                if not transaction:
                    flash('Transaction not found or already reviewed.', 'warning')
                elif not club:
                    flash('Selected club not found.', 'danger')
                else:
                    transaction.club_id = club.id
                    transaction.assigned_club_name = club.name
                    transaction.status = FoundationTransaction.STATUS_RECONCILED
                    transaction.updated_at = datetime.utcnow()
                    # transaction.reviewed_by_user_id = current_user.id # Optional
                    db_session.commit()
                    flash(f'Transaction {transaction.journal_ref or transaction.drs_description or transaction.id} successfully assigned to {club.name}.', 'success')
                    current_app.logger.info(f"Transaction ID {transaction_id} assigned to Club ID {club_id} by User ID {current_user.id}")
                    
                    # Potentially, re-generate the summary file here if reviews should immediately update it.
                    # This would be a more complex operation, involving re-reading from DB,
                    # re-applying logic from processing_utils to the existing temp file or regenerating it.
                    # For now, the downloaded file reflects the state *after initial processing*.

        except ValueError:
             flash('Invalid transaction or club ID format.', 'danger')
        except Exception as e:
            # db_session.rollback() # Handled by context manager if commit fails
            flash(f'An error occurred while assigning the club: {e}', 'danger')
            current_app.logger.error(f"Error assigning club for TX_ID {transaction_id}: {e}", exc_info=True)
            traceback.print_exc()

        return redirect(url_for('.foundation_review')) 

    transactions_to_review = []
    active_clubs = []
    try:
        with SessionLocal() as db_session: 
            transactions_to_review = db_session.query(FoundationTransaction).filter(
                FoundationTransaction.status == FoundationTransaction.STATUS_NEEDS_REVIEW
            ).order_by(FoundationTransaction.transaction_date.asc()).all() 

            active_clubs = db_session.query(Club).filter_by(is_active=True).order_by(Club.name).all()
    except Exception as e:
        current_app.logger.error(f"Error querying data for review page: {e}")
        flash("Could not retrieve data for the review page.", "danger")

    return render_template(
        'sports_clubs/foundation_review.html',
        transactions=transactions_to_review,
        clubs=active_clubs
    )
