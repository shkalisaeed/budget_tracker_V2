# Login and Signup functions go here
import datetime
import random
import string
from datetime import date, timedelta
from math import floor


from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from . import db
from . import CAPTCHA_TEXT
from .forms import ChangePasswordForm, DeletionForm, LoginForm, SignupForm
from .models import (Budget, Custom_Investment, Expense,
                     Stock_and_Crypto, User, Bill, SharedBudget, Goal, Income, ContributionHistory)

# Defines the blueprint for auth
auth = Blueprint("auth", __name__)

# Timer to lock a user out after some attempts in minutes
LOCKOUT_TIME = 0.5
FAILED_ATTEMPTS = 5

# Formats the date string in SQL to be usable with datetime


def format_dt(dt):
    return datetime.datetime(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]),
                             int(dt[11:13]), int(dt[14:16]), int(dt[17:19]))


@auth.route('/lockout/<int:user_id>')
def lockout(user_id):
    """
    This function calculates the remaining time for a user's lockout period and renders a lockout
    template with the remaining time.

    :param user_id: The user ID is a unique identifier for a specific user in the system. It is used to
    retrieve the user's information from the database
    :return: a rendered HTML template with the remaining time in seconds until the user's lockout period
    ends.
    """
    user = User.query.get(user_id)
    if user:
        start = datetime.datetime.now()
        end = format_dt(user.lock_end)
        remaining = floor((end - start).total_seconds())
    return render_template('/lockout.html', remaining=remaining)


@auth.route('/login', methods=['POST', 'GET'])
def login():
    """
    This function handles user login attempts, including locking out users after multiple failed
    attempts.
    :return: either a redirect to the home page or the lockout page if the user's account is locked, or
    it returns a rendered login template with the login form and appropriate flash messages.
    """

    # Instantiate a LoginForm from classes.py to accept an email, password and remember me option
    login_form = LoginForm()

    if login_form.validate_on_submit():

        user = User.query.filter_by(
            email=login_form.email.data.lower()).first()

        # Lock the user account after several failed attempts
        if user:
            if user.attempts >= FAILED_ATTEMPTS:

                # If the user's lockout timer hasn't started, start it.
                if user.lock_start == '':

                    user.lock_start = datetime.datetime.now()
                    user.lock_end = user.lock_start + \
                        timedelta(minutes=LOCKOUT_TIME)
                    db.session.commit()
                    return redirect(url_for("auth.lockout", user_id=user.user_id))

                elif format_dt(user.lock_end) > datetime.datetime.now():
                    return redirect(url_for("auth.lockout", user_id=user.user_id))

                elif format_dt(user.lock_end) <= datetime.datetime.now():
                    user.attempts = 0
                    user.lock_start = ''
                    user.lock_end = ''
                    db.session.commit()

        # Check if the user is in the database seeing if the assigned user var exists and checking if pswd match
        # Reset login attempts to 0
        if user:
            if check_password_hash(user.password, login_form.password.data):
                login_user(user, remember=login_form.remember.data)
                user.attempts = 0
                user.lock_start = ''
                user.lock_end = ''
                db.session.commit()

                return redirect(url_for("views.home"))

        # If the previous if block didn't return a redirect (i.e. failed login)
        flash("Invalid email/password combination. Please try again.")

        # Increment attempted logins from the user
        if user:
            flash(
                f"You will be locked out after {5 - user.attempts} attempts.")
            user.attempts += 1
            db.session.commit()

        return render_template('login.html', login_form=login_form)

    return render_template('login.html', login_form=login_form)


@auth.route('/logout')
@login_required
def logout():
    """
    This function logs out the user and redirects them to the home page.
    :return: a redirect to the home page of the website.
    """
    logout_user()
    return redirect(url_for("views.home"))


@auth.route('/signup', methods=['POST', 'GET'])
def signup():
    """
    This function handles the signup process for a user, validating their input and storing their
    information in a database.
    :return: either a rendered template of the signup page with the SignupForm object passed to it, or a
    redirect to the home page if the user successfully signs up.
    """

    # Instantiate a SignupForm and pass it to signup.html
    signup_form = SignupForm()

    # Store the user's pswd as a hash to improve security
    if signup_form.validate_on_submit():

        # Check if they pass the captcha
        if signup_form.captcha.data != CAPTCHA_TEXT:
            flash("Incorrect CAPTCHA. Please try again.")
            return render_template('signup.html', signup_form=signup_form)

        if signup_form.password.data != signup_form.password2.data:
            flash("Passwords don't match.")
            return render_template('signup.html', signup_form=signup_form)

        hash_pswd = generate_password_hash(
            signup_form.password.data, method="sha256")
        new_email = signup_form.email.data.lower()
        new_f_name = signup_form.first_name.data
        new_l_name = signup_form.last_name.data
        dob = signup_form.birthday.data

        # users need to be at least 18
        if dob >= date.today() - timedelta(days=365 * 18):
            flash("You must be at least 18 years old to sign up.")
            return render_template('signup.html', signup_form=signup_form)

        # Create a new User object and store it into the database
        new_user = User(first_name=new_f_name,
                        last_name=new_l_name, dob=dob, email=new_email, password=hash_pswd, date_created=datetime.date.today())

        # If the email already exists, prompt the user to enter a new email
        try:
            db.session.add(new_user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("This email address is already taken.")
            return render_template('signup.html', signup_form=signup_form)

        user = User.query.filter_by(email=new_email).first()
        login_user(user)

        return redirect(url_for("views.home"))

    return render_template('signup.html', signup_form=signup_form)


@auth.route('/change_password/<int:user_id>', methods=['GET', 'POST'])
@login_required
def change_password(user_id):
    """
    This function allows a user to change their password by validating their old password and ensuring
    the new passwords match.

    :param user_id: The user ID of the user whose password is being changed
    :return: a rendered template of the 'change_password.html' page with the user_id and
    change_pswd_form variables passed as arguments. If the form is validated and the password is
    successfully updated, the function also flashes a success message before rendering the template. If
    there is an error updating the password, the function returns an error message instead of rendering
    the template.
    """

    change_pswd_form = ChangePasswordForm()

    if change_pswd_form.validate_on_submit():

        # Check if the user is in the database seeing if the assigned user var exists and checking if pswd match
        user = User.query.get(user_id)
        if user:
            # Old password matches the db and new passwords match
            if check_password_hash(user.password, change_pswd_form.old_pswd.data) and \
                    change_pswd_form.new_pswd.data == change_pswd_form.new_pswd_2.data:
                new_paswd = change_pswd_form.new_pswd.data
                hash_pswd = generate_password_hash(new_paswd, method="sha256")
                user.password = hash_pswd
                try:
                    db.session.commit()
                    flash("Password successfully updated.")
                    return render_template('change_password.html', id=current_user.user_id, change_pswd_form=change_pswd_form)
                except:
                    return "Error updating :("
            elif not check_password_hash(user.password, change_pswd_form.old_pswd.data):
                flash("Please retype your old password.")
                return render_template('change_password.html', user_id=current_user.user_id, change_pswd_form=change_pswd_form)
            elif change_pswd_form.new_pswd.data != change_pswd_form.new_pswd_2.data:
                flash("Passwords don't match.")
                return render_template('change_password.html', id=current_user.user_id, change_pswd_form=change_pswd_form)

        return render_template('change_password.html', id=current_user.user_id, change_pswd_form=change_pswd_form)

    return render_template('change_password.html', id=current_user.user_id, change_pswd_form=change_pswd_form)


@auth.route('/delete_account/<int:user_id>', methods=['GET', 'POST'])
@login_required
def delete_account(user_id):
    """
    This function deletes a user account and all associated data from a budgeting application.

    :param user_id: The ID of the user whose account is being deleted
    :return: a rendered template of the 'delete_account.html' page with the deletion_form as a
    parameter. If the deletion_form is validated and the password is correct, the function redirects to
    the home page. If the password is incorrect, the function flashes a message and renders the
    'delete_account.html' page again with the deletion_form as a parameter.
    """

    # FIXME: Update the deletion process as tables get updated
    deletion_form = DeletionForm()

    if deletion_form.validate_on_submit():

        user = User.query.get(user_id)
        budgets = Budget.query.filter_by(user_id=user_id).all()
        expenses = Expense.query.filter_by(user_id=user_id).all()
        investments = Investment.query.filter_by(user_id=user_id).all()
        stocks_and_crypto = Stock_and_Crypto.query.filter_by(
            user_id=user_id).all()
        custom_investments = Custom_Investment.query.filter_by(
            user_id=user_id).all()
        bills = Bill.query.filter_by(
            user_id=user_id).all()
        goals = Goal.query.filter_by(
            user_id=user_id).all()
        shared_budgets = SharedBudget.query.filter_by(
            user_id=user_id).all()
        incomes = Income.query.filter_by(user_id=user_id).all()
        goal_ids = [goal.goal_id for goal in goals]

        if check_password_hash(user.password, deletion_form.pswd.data):
            logout_user()
            db.session.delete(user)

            for budget in budgets:
                db.session.delete(budget)

            for expense in expenses:
                db.session.delete(expense)

            for investment in investments:
                db.session.delete(investment)

            for stock in stocks_and_crypto:
                db.session.delete(stock)

            for custom_investment in custom_investments:
                db.session.delete(custom_investment)

            for bill in bills:
                db.session.delete(bill)

            for goal_id in goal_ids:
                history = ContributionHistory.query.filter_by(
                    goal_id=goal_id).all()
                for entry in history:
                    db.session.delete(entry)

            for goal in goals:
                db.session.delete(goal)

            for shared_budget in shared_budgets:
                db.session.delete(shared_budget)

            for income in incomes:
                db.session.delete(income)

            db.session.commit()
            return redirect(url_for('views.home'))

        else:
            flash("Incorrect passowrd.")
            return render_template('delete_account.html', deletion_form=deletion_form)

    # logout_user()
    # return redirect(url_for("views.home"))
    return render_template('delete_account.html', deletion_form=deletion_form)
