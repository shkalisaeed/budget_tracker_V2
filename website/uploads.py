
import csv
import datetime
import os
import zipfile
from time import strptime

import joblib
from dateutil.relativedelta import relativedelta
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from . import db
from .classification import categorise_description
from .forms import (BillsForm, ExpenseForm, GoalsForm, IncomeForm,
                    InvestmentForm)
from .models import Bill, Expense, Goal, Income

# Defines the blueprint for auth
uploads = Blueprint("uploads", __name__)


@uploads.route('/upload_csv', methods=['POST', 'GET'])
@login_required
def upload_csv():
    """
    This function uploads a CSV file, reads its contents, categorizes the expenses, and inserts them
    into the Expenses table in a database.
    :return: the rendered template 'upload_csv.html'.
    """
    if request.method == "POST":

        # Get expense account type
        account_type = request.form["account-type"]
        if account_type == "other":
            account_type = request.form["new-account"]

        csv_file = request.files["file"]
        # Check if the file type is .csv
        if csv_file and '.' in csv_file.filename and csv_file.filename.rsplit('.', 1)[1].lower() == "csv":
            filename = secure_filename(csv_file.filename)
            csv_file.save(os.path.join("website", "Static", filename))

            # Get the zipped file containing the model
            model_filename = os.path.join(
                "website", "category_nlp.joblib")
            current_path = os.getcwd()
            file_path = os.path.join(current_path, model_filename)
            if os.path.exists(file_path):
                pass
            else:
                with zipfile.ZipFile(os.path.join(
                        "website", "category_nlp.zip"), 'r') as zipf:
                    zipf.extractall(os.path.join(current_path, "website"))

            # Load the saved model data from file
            model_data = joblib.load(file_path)

            # Read from file
            with open(os.path.join("website", "Static", filename)) as f:
                csv_reader = csv.reader(f)
                next(csv_reader)
                for line in csv_reader:
                    # ignore blank lines
                    if line[0] == '' or line[1] == '' or line[2] == '':
                        continue

                    date = line[0]
                    description = line[2]
                    date = datetime.datetime.strptime(
                        date, "%d/%m/%Y").strftime("%Y-%m-%d")
                    amount = float(line[1])
                    # store expenses (i.e. negative values) and convert them to positive, skip positive amounts (i.e. income)
                    if amount < 0:
                        # flash(f"{line[0]} {line[1]} {line[2]}")
                        # print(categorise_description(description))
                        amount = abs(amount)
                        # Insert into the Expenses table

                        # CHange category from housing -> housing and utils
                        category = categorise_description(
                            model_data, description)
                        if category == "Housing":
                            category = "Housing and Utilities"
                        new_expenses = Expense(
                            user_id=current_user.user_id, expense_amount=amount, description=description,
                            expense_date=date, expense_category=category, account_type=account_type)
                        db.session.add(new_expenses)
                        db.session.commit()
                    # Store positive amounts as income
                    elif amount > 0:
                        new_income = Income(user_id=current_user.user_id, income_amount=amount, income_description=description,
                                            income_date=date, account_type=account_type)
                        db.session.add(new_income)
                        db.session.commit()

            flash(f"{filename} has been uploaded successfully.")

            # Delete the file after reading
            os.remove(os.path.join("website", "Static", filename))

        else:
            flash("Invalid file. Please upload a csv file.")

    return render_template('upload_csv.html')


@uploads.route('/upload_expenses', methods=['POST', 'GET'])
@login_required
def upload_expenses():
    """
    This function uploads user inputted expenses to a database after validating the input.
    :return: a rendered HTML template for the 'upload_expenses.html' page, with the expense_form object
    passed as a parameter. If the expense_form is validated and the new expense is added to the
    database, a flash message is also displayed.
    """

    # Instantiate an ExpenseForm to store user input
    expense_form = ExpenseForm()

    if expense_form.validate_on_submit():

        # Get expense account type
        account_type = request.form["account-type"]
        if account_type == "other":
            account_type = request.form["new-account"]

        new_expenses = Expense(
            user_id=current_user.user_id, expense_amount=expense_form.amount.data,
            description=expense_form.description.data, expense_date=expense_form.date.data,
            expense_category=expense_form.category.data, account_type=account_type)
        db.session.add(new_expenses)
        db.session.commit()
        flash("Input received.")

        return render_template('upload_expenses.html', expense_form=expense_form)

    return render_template('upload_expenses.html', expense_form=expense_form)


@uploads.route('/upload_investment', methods=['POST', 'GET'])
@login_required
def upload_investment():
    """
    This function handles the uploading of new investments into the Investment and S&C tables and
    renders the upload_investment.html template with an InvestmentForm.
    :return: a rendered HTML template called 'upload_investment.html' with the investment_form object
    passed as a parameter.
    """

    # Instantiate an InvestmentForm to store user input
    investment_form = InvestmentForm()

    # TODO: Insert new investment into Investment and S&C tables

    if investment_form.validate_on_submit():

        #     new_expenses = Investment(
        #         user_id=current_user.user_id, expense_amount=expense_form.amount.data, description=expense_form.description.data, expense_date=expense_date, expense_category=expense_form.category.data)
        #     db.session.add(new_expenses)
        # db.session.commit()
        flash("Input received.")

        return render_template('upload_investment.html', investment_form=investment_form)

    return render_template('upload_investment.html', investment_form=investment_form)


@uploads.route('/upload_bills', methods=['POST', 'GET'])
@login_required
def upload_bills():
    """
    This function handles the submission of a form for uploading bills and adds the bill information to
    the database.
    :return: a redirect to the 'upload_bills' route with the bills_form object as a parameter if the
    bills_form has been validated on submit. Otherwise, it is rendering the 'upload_bills.html' template
    with the bills_form object as a parameter.
    """

    # Instantiate an BillsForm to store user input
    bills_form = BillsForm()

    # user clicks input bills, fthis is function for submitting fix later
    if bills_form.validate_on_submit():
        flash("Input received.")
        # on submit, store some stuff in db
        # Calculate the time between the two bills
        # period = (max([bills_form.bill_1.data, bills_form.bill_2.data]) -
        #           min([bills_form.bill_1.data, bills_form.bill_2.data])).days

        # flash(bills_form.bill_name.data)
        # flash(bills_form.bill_desc.data)
        # flash(bills_form.bill_due_date.data)
        # flash(bills_form.bill_options.data)
        # flash(bills_form.bill_custom_freq.data)

        if bills_form.bill_options.data in ['Monthly', 'Quarterly',
                                            "Biannual", "Annual"]:
            new_bill = Bill(user_id=current_user.user_id, bill_name=bills_form.bill_name.data,
                            bill_description=bills_form.bill_desc.data, bill_due_date=bills_form.bill_due_date.data,
                            bill_options=bills_form.bill_options.data, bill_custom_freq=-1)
            db.session.add(new_bill)
            db.session.commit()
        else:
            new_bill = Bill(user_id=current_user.user_id, bill_name=bills_form.bill_name.data,
                            bill_description=bills_form.bill_desc.data, bill_due_date=bills_form.bill_due_date.data,
                            bill_options=bills_form.bill_options.data, bill_custom_freq=bills_form.bill_custom_freq.data)
            db.session.add(new_bill)
            db.session.commit()

        # flash("Time between these two bills:")
        # flash(period)
        # flash("Input received.")

    # cycle_period - either fixed day of month or every x days
    # date sanitisatuin yyyy-mm-dd

        return redirect(url_for('uploads.upload_bills', bills_form=bills_form))

    return render_template('upload_bills.html', bills_form=bills_form)


@uploads.route('/upload_goals', methods=['POST', 'GET'])
@login_required
def upload_goals():
    """
    This function uploads a new goal to the database if the form is validated.
    :return: a rendered template 'upload_goals.html' with the goals_form object passed as a parameter.
    If the form is validated, a new goal is created and added to the database, and a flash message is
    displayed.
    """

    goals_form = GoalsForm()

    if goals_form.validate_on_submit():

        # Ensure that the date provided isn't in the past
        if goals_form.goal_date.data < datetime.datetime.today().date():
            flash("Goal date cannot be in the past.")
            return render_template('upload_goals.html', goals_form=goals_form)

        # Ensure that the target amount isn't negative or 0
        if float(goals_form.goal_amount.data) <= 0:
            flash("Invalid goal amount.")
            return render_template('upload_goals.html', goals_form=goals_form)

        # Calculate the next contribution date and the amount
        if goals_form.contribution_frequency.data == "Weekly":
            next_date = datetime.date.today() + relativedelta(days=7)
            delta = goals_form.goal_date.data - datetime.date.today()
            payments = delta.days / 7
            next_payment = goals_form.goal_amount.data / payments

        elif goals_form.contribution_frequency.data == "Fortnightly":
            next_date = datetime.date.today() + relativedelta(days=14)
            delta = goals_form.goal_date.data - datetime.date.today()
            payments = delta.days / 14
            next_payment = goals_form.goal_amount.data / payments

        elif goals_form.contribution_frequency.data == "Monthly":
            next_date = datetime.date.today() + relativedelta(months=1)
            delta = goals_form.goal_date.data - datetime.date.today()
            payment_per_day = goals_form.goal_amount.data / delta.days
            next_payment = (next_date - datetime.date.today()
                            ).days * payment_per_day

        # if next contribution date is after the goal due date, set it as the goal due date.
        if next_date > goals_form.goal_date.data:
            next_date = goals_form.goal_date.data

        new_goal = Goal(user_id=current_user.user_id, goal_name=goals_form.goal_name.data,
                        goal_amount=goals_form.goal_amount.data, goal_description=goals_form.goal_desc.data,
                        goal_date=goals_form.goal_date.data, contribution_frequency=goals_form.contribution_frequency.data,
                        next_contribution_date=next_date, next_contribution_amount=next_payment, cyclical_contribution=next_payment)
        db.session.add(new_goal)
        db.session.commit()

        flash("Goal Uploaded.")

    return render_template('upload_goals.html', goals_form=goals_form)


@uploads.route('/income', methods=['POST', 'GET'])
@login_required
def income():

    # Query the db for user income
    user_income = Income.query.filter_by(
        user_id=current_user.user_id).all()

    # Instantiate an ExpenseForm to store user input
    income_form = IncomeForm()

    if income_form.validate_on_submit():

        # Get expense account type
        account_type = request.form["account-type"]
        if account_type == "other":
            account_type = request.form["new-account"]

        new_income = Income(
            user_id=current_user.user_id, income_amount=income_form.amount.data,
            income_description=income_form.description.data, income_date=income_form.date.data,
            account_type=account_type)
        db.session.add(new_income)
        db.session.commit()
        flash("Input received.")

        return redirect(url_for("uploads.income"))

    return render_template('income.html', income_form=income_form, user_income=user_income)
