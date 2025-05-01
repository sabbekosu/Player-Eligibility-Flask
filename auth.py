# auth.py
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash # For registration/user creation
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField # Added SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

# Import User model and SessionLocal
from models import User
from db import SessionLocal

auth = Blueprint('auth', __name__, template_folder='templates')

# --- Forms ---
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Role', choices=[('sspa', 'SSPA'), ('admin', 'Admin')], validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register User')

    # Custom validators to check if username/email already exist
    def validate_username(self, username):
        with SessionLocal() as db:
            user = db.query(User).filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username already taken. Please choose a different one.')

    def validate_email(self, email):
         with SessionLocal() as db:
            user = db.query(User).filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email already registered. Please choose a different one.')

# --- Routes ---
@auth.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('home')) # Redirect to main home page

    form = LoginForm()
    if form.validate_on_submit():
        with SessionLocal() as db:
            user = db.query(User).filter_by(username=form.username.data).first()
        # Check if user exists and password is correct
        if user and user.check_password(form.password.data):
            login_user(user) # Log in the user
            flash('Login successful!', 'success')
            # Redirect to the page the user was trying to access, or home
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        else:
            flash('Login unsuccessful. Please check username and password.', 'danger')
    return render_template('auth/login.html', title='Login', form=form)

@auth.route('/logout')
@login_required # User must be logged in to log out
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

# --- Registration Route (Optional - Consider if self-registration is needed) ---
# Protect this route, e.g., only allow admins to register new users
@auth.route('/register', methods=['GET', 'POST'])
@login_required # Example: Only logged-in users can register others
def register():
    # Add role check if needed:
    if current_user.role != 'admin':
         flash('Only administrators can register new users.', 'danger')
         return redirect(url_for('home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data
        )
        new_user.set_password(form.password.data) # Hash the password

        with SessionLocal() as db:
            db.add(new_user)
            try:
                db.commit()
                flash(f'Account created for {form.username.data}!', 'success')
                return redirect(url_for('auth.login')) # Or redirect to an admin user list
            except Exception as e:
                db.rollback()
                flash(f'Error creating account: {e}', 'danger')
                print(f"Error committing new user: {e}")

    return render_template('auth/register.html', title='Register New User', form=form)

# --- Utility Function (Optional - for creating first admin user via shell) ---
def create_admin_user(username, email, password):
    """Helper to create the first admin user."""
    with SessionLocal() as db:
        if db.query(User).filter_by(username=username).first():
            print(f"User '{username}' already exists.")
            return
        admin_user = User(username=username, email=email, role='admin')
        admin_user.set_password(password)
        db.add(admin_user)
        try:
            db.commit()
            print(f"Admin user '{username}' created successfully.")
        except Exception as e:
            db.rollback()
            print(f"Error creating admin user: {e}")

# Example usage (run in python shell or a dedicated script):
# if __name__ == '__main__':
#     # Make sure this runs in the context where db and User are defined
#     print("Creating initial admin user...")
#     create_admin_user('admin', 'admin@example.com', 'password') # CHANGE PASSWORD
