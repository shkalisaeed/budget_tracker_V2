# Other pages go here

import base64
import datetime
import os
import zipfile
import heapq
import calendar
from collections import defaultdict
from datetime import date
from io import BytesIO
from collections import Counter

from decimal import Decimal
import joblib
import matplotlib
import matplotlib.font_manager as font_manager
import matplotlib.pyplot as plt
import numpy as np
from dateutil.relativedelta import relativedelta
from flask import (Blueprint, abort, current_app, make_response, redirect,
                   render_template, request, send_file, url_for, flash)
from flask_login import current_user, login_required
from ics import Calendar, Event
from random import uniform

from . import db
from .forms import BudgetSharingForm
from .classification import get_sequences
from .models import Bill, Budget, Expense, Stock_and_Crypto, Goal, SharedBudget, User, Income, Custom_Investment, ContributionHistory

matplotlib.use('agg')

# Defines the blueprint for views
views = Blueprint("views", __name__)

# Home page
# for section 5 stocks and crypto


@views.route('/', methods=['POST', 'GET'])
def home():
    """
    This function retrieves and processes data from the database to display on the home page.
    :return: a rendered HTML template with various variables passed in depending on whether the user is
    logged in or not. If the user is logged in, the function queries the database for various data such
    as the user's expenses, budget, bills, and investments, and calculates various statistics such as
    upcoming bills, spending breakdowns, and remaining budget. The function then passes these variables
    into the HTML template
    """

    logged_in = current_user.is_authenticated

    if logged_in:

        # Cleanup the static folder by removing .csv and .ics files
        cleanup_static()

        # top 3 spenders based on expense description
        top_five = top_expenses()

        cryptocurrency = Stock_and_Crypto.query.filter_by(
            user_id=current_user.user_id).all()

        cryptocurrency2 = Custom_Investment.query.filter_by(
            user_id=current_user.user_id).all()

        user_expenses = Expense.query.filter_by(
            user_id=current_user.user_id).all()

        user_budget = Budget.query.filter_by(
            user_id=current_user.user_id).all()

        user_bills = Bill.query.filter_by(
            user_id=current_user.user_id).all()

        user_investments = Stock_and_Crypto.query.filter_by(
            user_id=current_user.user_id).all()

        goals = Goal.query.filter_by(user_id=current_user.user_id).all()

        # Extract the columns as separate variables
        goal_ids = [goal.goal_id for goal in goals]
        user_ids = [goal.user_id for goal in goals]
        goal_names = [goal.goal_name for goal in goals]
        goal_amounts = [goal.goal_amount for goal in goals]
        goal_descriptions = [goal.goal_description for goal in goals]
        goal_dates = [goal.goal_date for goal in goals]
        total_contributions = [goal.total_contribution for goal in goals]
        next_contribution_dates = [
            goal.next_contribution_date for goal in goals]
        next_contribution_amounts = [
            goal.next_contribution_amount for goal in goals]

        # Update the due date if the date has passed
        for bill in user_bills:
            while datetime.date.fromisoformat(str(bill.bill_due_date)) < datetime.date.today():
                # If the user has custom cycle, continuously add to the cycle to the past due date until the due date is in the future
                if bill.bill_options == "Custom Days":
                    bill.bill_due_date = datetime.date.fromisoformat(str(bill.bill_due_date)) + datetime.timedelta(
                        days=bill.bill_custom_freq)
                # Else if the user has set day every month/quarter/6 months/year, add the month accordingly
                elif bill.bill_options == "Monthly":
                    bill.bill_due_date = datetime.date.fromisoformat(
                        str(bill.bill_due_date)) + relativedelta(months=1)
                elif bill.bill_options == "Quarterly":
                    bill.bill_due_date = datetime.date.fromisoformat(
                        str(bill.bill_due_date)) + relativedelta(months=3)
                elif bill.bill_options == "Biannual":
                    bill.bill_due_date = datetime.date.fromisoformat(
                        str(bill.bill_due_date)) + relativedelta(months=6)
                elif bill.bill_options == "Annual":
                    bill.bill_due_date = datetime.date.fromisoformat(
                        str(bill.bill_due_date)) + relativedelta(months=12)

        db.session.commit()

        # Query for upcoming bills in the next UPCOMING_BILLS days
        UPCOMING_BILL_DAYS = 30
        upcoming_bills = Bill.query.filter(
            Bill.user_id == current_user.user_id, Bill.bill_due_date.between(datetime.date.today(), datetime.date.today() + datetime.timedelta(days=UPCOMING_BILL_DAYS))).all()
        # upcoming_user_bills = upcoming_bills.query.filter(upcoming_bills.date_column.between(
        #     datetime.date.today(), datetime.date.today() + datetime.timedelta(days=7))).all()

        # If the user hasn't made a budget yet
        if len(user_budget) == 0:
            # Query the database and add to the dictionary
            years = defaultdict(list)
            for i in range(len(user_expenses)):
                transaction = {}

                # mcc = user_expenses[i].mcc
                transaction['category'] = user_expenses[i].expense_category
                transaction['spent'] = float(user_expenses[i].expense_amount)
                transaction['budget'] = 0.0

                date = user_expenses[i].expense_date

                years[date[:7]].append(transaction)

            years_sorted = dict(sorted(years.items()))

            # Convert date to "Month Year"
            years = defaultdict(list)
            for key in years_sorted:
                date_obj = datetime.datetime.strptime(key, '%Y-%m')
                month_year = date_obj.strftime('%B %Y')
                years[month_year] = years_sorted[key]

            # Sum up the transactions in each month if theyre the same category
            for key, value_list in years.items():
                category_totals = {}
                for value in value_list:
                    category = value['category']
                    if category in category_totals:
                        category_totals[category]['spent'] += value['spent']
                        category_totals[category]['budget'] += value['budget']
                    else:
                        category_totals[category] = {
                            'category': category,
                            'spent': value['spent'],
                            'budget': value['budget']
                        }
                years[key] = list(category_totals.values())

            months = list(years.keys())
            if len(months) == 0:
                return render_template("home.html", top_five=top_five, logged_in=logged_in,
                                       upcoming_bills=upcoming_bills, user_expenses=user_expenses,
                                       UPCOMING_BILL_DAYS=UPCOMING_BILL_DAYS, cryptocurrency=cryptocurrency, cryptocurrency2=cryptocurrency2,
                                       goal_names=goal_names, goal_amounts=goal_amounts, goal_descriptions=goal_descriptions,
                                       goal_dates=goal_dates, total_contributions=total_contributions, goal_ids=goal_ids,
                                       next_contribution_dates=next_contribution_dates, next_contribution_amounts=next_contribution_amounts)
            # print(list(months))
            # Let the user choose a month
            current_date = datetime.date.today()
            formatted_date = current_date.strftime("%B %Y")
            selected_month = formatted_date
            # Query the database given the chosen month
            # Query to get the categories for the month and the spendings for each category
            if selected_month not in list(years.keys()):
                return render_template("home.html", top_five=top_five, logged_in=logged_in,
                                       upcoming_bills=upcoming_bills, UPCOMING_BILL_DAYS=UPCOMING_BILL_DAYS,
                                       cryptocurrency=cryptocurrency, cryptocurrency2=cryptocurrency2, goal_names=goal_names,
                                       goal_amounts=goal_amounts, goal_descriptions=goal_descriptions,
                                       goal_dates=goal_dates, total_contributions=total_contributions, goal_ids=goal_ids,
                                       next_contribution_dates=next_contribution_dates, next_contribution_amounts=next_contribution_amounts)

            spendings = years[selected_month]
            # List of expenses for each category
            categories = [list(i.values())[0] for i in spendings]
            expenses = [list(i.values())[1] for i in spendings]

            breakdown_rows = [[categories[i], expenses[i]]
                              for i in range(len(categories))]
            breakdown_rows.insert(0, ['Categories', 'Amount'])

            # THE TOTAL REMAINING DONUT PLOT
            total_budget_set = sum([list(i.values())[2] for i in spendings])
            total_budget = sum(expenses)
            total_remaining = total_budget_set - total_budget
            if total_remaining < 0.0:
                total_remaining = 0.0

            acc_type_trans = defaultdict(list)
            for i in range(len(user_expenses)):
                expense = float(user_expenses[i].expense_amount)
                # acc_type['account_type'] = user_expenses[i].account_type
                acc_type_trans[user_expenses[i].account_type].append(expense)

            y = []
            x = []
            for key in acc_type_trans.keys():
                y.append(key)
                x.append(sum(acc_type_trans[key]))
            colors = ['#e7e1ef', '#d4b9da', '#c994c7', '#df65b0', '#e7298a',
                      '#ce1256', '#980043', '#67001f', '#49000a', '#320003']
            bar_array = []
            for i in range(len(x)):
                bar_array.append([y[i], x[i], colors[i % 10]])

            spendings = sorted(spendings, key=lambda x: (
                x['spent'], x['budget']), reverse=True)

            return render_template("home.html", logged_in=logged_in, spendings=spendings,
                                   total_remaining=total_remaining, total_budget=total_budget,
                                   breakdown_rows=breakdown_rows, total_budget_set=total_budget_set,
                                   upcoming_bills=upcoming_bills, user_expenses=user_expenses,
                                   user_budget=user_budget, bar_array=bar_array, UPCOMING_BILL_DAYS=UPCOMING_BILL_DAYS,
                                   cryptocurrency=cryptocurrency, cryptocurrency2=cryptocurrency2, goals=goals, goal_ids=goal_ids,
                                   user_ids=user_ids, goal_names=goal_names, goal_amounts=goal_amounts,
                                   goal_descriptions=goal_descriptions, goal_dates=goal_dates,
                                   total_contributions=total_contributions, top_five=top_five,
                                   next_contribution_dates=next_contribution_dates, next_contribution_amounts=next_contribution_amounts)

        budget_month = user_budget[len(user_budget)-1].date_start[:7]
        budget_categories = [x.strip() for x in user_budget[len(
            user_budget)-1].categories.split(',')]
        budget_amounts = [float(x.strip())
                          for x in user_budget[len(user_budget)-1].amounts.split(',')]

        budget = defaultdict(list)
        for i in range(len(budget_categories)):
            budget_line = {}
            budget_line['category'] = budget_categories[i]
            budget_line['budget'] = budget_amounts[i]

            budget[user_budget[len(user_budget)-1].date_start[:7]
                   ].append(budget_line)

        budget_sorted = {}
        for key in budget:
            date_obj = datetime.datetime.strptime(key, '%Y-%m')
            month_year = date_obj.strftime('%B %Y')
            budget_sorted[month_year] = budget[key]

        # Query the database and add to the dictionary
        years = defaultdict(list)
        for i in range(len(user_expenses)):
            transaction = {}

            # mcc = user_expenses[i].mcc
            transaction['category'] = user_expenses[i].expense_category
            transaction['spent'] = float(user_expenses[i].expense_amount)
            transaction['budget'] = 0.0

            date = user_expenses[i].expense_date

            years[date[:7]].append(transaction)

        years_sorted = dict(sorted(years.items()))

        # Convert date to "Month Year"
        years = defaultdict(list)
        for key in years_sorted:
            date_obj = datetime.datetime.strptime(key, '%Y-%m')
            month_year = date_obj.strftime('%B %Y')
            years[month_year] = years_sorted[key]

        # Sum up the transactions in each month if theyre the same category
        for key, value_list in years.items():
            category_totals = {}
            for value in value_list:
                category = value['category']
                if category in category_totals:
                    category_totals[category]['spent'] += value['spent']
                    category_totals[category]['budget'] += value['budget']
                else:
                    category_totals[category] = {
                        'category': category,
                        'spent': value['spent'],
                        'budget': value['budget']
                    }
            years[key] = list(category_totals.values())

        months = list(years.keys())
        if len(months) == 0:
            return render_template("home.html", top_five=top_five, logged_in=logged_in,
                                   upcoming_bills=upcoming_bills, user_expenses=user_expenses,
                                   user_budget=user_budget, UPCOMING_BILL_DAYS=UPCOMING_BILL_DAYS,
                                   cryptocurrency=cryptocurrency, cryptocurrency2=cryptocurrency2, goal_names=goal_names,
                                   goal_amounts=goal_amounts, goal_descriptions=goal_descriptions,
                                   goal_dates=goal_dates, total_contributions=total_contributions, goal_ids=goal_ids,
                                   next_contribution_dates=next_contribution_dates, next_contribution_amounts=next_contribution_amounts)

        current_date = datetime.date.today()
        formatted_date = current_date.strftime("%B %Y")
        selected_month = formatted_date

        # selected_month = months[len(months)-1]
        # Query the database given the chosen month
        # Query to get the categories for the month and the spendings for each category
        if selected_month not in list(years.keys()):
            return render_template("home.html", top_five=top_five, logged_in=logged_in,
                                   upcoming_bills=upcoming_bills, UPCOMING_BILL_DAYS=UPCOMING_BILL_DAYS,
                                   cryptocurrency=cryptocurrency, cryptocurrency2=cryptocurrency2, goal_names=goal_names,
                                   goal_amounts=goal_amounts, goal_descriptions=goal_descriptions,
                                   goal_dates=goal_dates, total_contributions=total_contributions, goal_ids=goal_ids,
                                   next_contribution_dates=next_contribution_dates, next_contribution_amounts=next_contribution_amounts)

        # Update the dict with all the budget values
        for key in list(years.keys()):
            # compare the months (right now only works with the latest month)
            if key == list(budget_sorted.keys())[0]:
                for item in budget_sorted[key]:
                    category = item['category']
                    budget_amount = item['budget']
                    if not any(d.get('category') == category for d in years[key]):
                        years[key].append(
                            {'category': category, 'spent': 0.0, 'budget': budget_amount})
                    else:
                        for d in years[key]:
                            if d.get('category') == category:
                                d['budget'] = budget_amount

        spendings = years[selected_month]
        # List of categories
        categories = [list(i.values())[0] for i in spendings]
        # List of expenses for each category
        expenses = [list(i.values())[1] for i in spendings]

        breakdown_cat = [entry['category']
                         for entry in spendings if entry['spent'] != 0.0]
        breakdown_spent = [entry['spent']
                           for entry in spendings if entry['spent'] != 0.0]
        breakdown_rows = [[breakdown_cat[i], breakdown_spent[i]]
                          for i in range(len(breakdown_cat))]
        breakdown_rows.insert(0, ['Categories', 'Amount'])
        # BREAKDOWN PIE PLOT
        cmap = plt.cm.get_cmap('PuRd', 10)
        # Create list of colors
        colors = [cmap(i) for i in range(10)]

        # THE TOTAL REMAINING DONUT PLOT
        total_budget_set = sum([list(i.values())[2] for i in spendings])
        total_budget = sum(expenses)
        total_remaining = total_budget_set - total_budget
        if total_remaining < 0.0:
            total_remaining = 0.0

        print(total_remaining)

        acc_type_trans = defaultdict(list)
        for i in range(len(user_expenses)):
            expense = float(user_expenses[i].expense_amount)
            # acc_type['account_type'] = user_expenses[i].account_type
            acc_type_trans[user_expenses[i].account_type].append(expense)

        y = []
        x = []
        for key in acc_type_trans.keys():
            y.append(key)
            x.append(sum(acc_type_trans[key]))
        colors = ['#e7e1ef', '#d4b9da', '#c994c7', '#df65b0', '#e7298a',
                  '#ce1256', '#980043', '#67001f', '#49000a', '#320003']
        bar_array = []
        for i in range(len(x)):
            bar_array.append([y[i], x[i], colors[i % 10]])
        print(bar_array)
        spendings = sorted(spendings, key=lambda x: (
            x['spent'], x['budget']), reverse=True)

        return render_template("home.html", top_five=top_five, user_expenses=user_expenses,
                               investments=user_investments, user_budget=user_budget,
                               logged_in=logged_in, spendings=spendings, total_remaining=total_remaining,
                               total_budget=total_budget, breakdown_rows=breakdown_rows,
                               total_budget_set=total_budget_set, bar_array=bar_array, upcoming_bills=upcoming_bills,
                               UPCOMING_BILL_DAYS=UPCOMING_BILL_DAYS, goals=goals, goal_ids=goal_ids,
                               user_ids=user_ids, goal_names=goal_names, goal_amounts=goal_amounts,
                               goal_descriptions=goal_descriptions, goal_dates=goal_dates,
                               total_contributions=total_contributions, cryptocurrency=cryptocurrency, cryptocurrency2=cryptocurrency2,
                               next_contribution_dates=next_contribution_dates, next_contribution_amounts=next_contribution_amounts)

    return render_template("home.html", logged_in=logged_in)


@views.route('/home', methods=['POST', 'GET'])
def landing():
    """
    This function returns the rendered template for a landing page.
    :return: The function `landing()` is returning the rendered template "landing_page.html".
    """

    return render_template("landing_page.html")


@views.route('/preferences', methods=['POST', 'GET'])
@login_required
def preferences():
    """
    This function returns the rendered template for the preferences.html file.
    :return: The function `preferences()` is returning the rendered HTML template "preferences.html".
    """

    return render_template("preferences.html")

# Crypto Page
# changes by Ali######


@views.route('/cryptocurrency', methods=['POST', 'GET'])
def cryptocurrency():
    """
    This function allows users to add cryptocurrency investments to their portfolio and displays their
    current holdings.
    :return: a rendered HTML template called 'cryptocurrency.html' with a variable called
    'cryptocurrency' that contains a list of Stock_and_Crypto objects filtered by the current user's
    user_id.
    """

    if request.method == "POST":
        amount = request.form["amount2"]
        share = request.form["share2"]
        symbol = request.form["shareSymbol2"]
        date = request.form["orderDate2"]

        new_crypto = Stock_and_Crypto(ticker_name=share, ticker_symbol=symbol,
                                      total_price=amount, order_date=date, user_id=current_user.user_id, investment_type="Crypto")
        db.session.add(new_crypto)
        db.session.commit()

    user_crypto = Stock_and_Crypto.query.filter_by(
        user_id=current_user.user_id).all()

    return render_template('cryptocurrency.html', cryptocurrency=user_crypto)


############


# Expenses summary page
# Shows the monthly chart the top
@views.route('/summary', methods=['POST', 'GET'])
@login_required
def summary():
    """
    This function generates a summary of a user's expenses and budget, including visualizations of
    spending breakdowns and historical spending.
    :return: a rendered HTML template with various variables passed in, including the months, selected
    month, total spending, breakdown of spending in a pie plot, remaining budget in a donut plot, and
    historical spending in a bar plot. The specific HTML template being rendered is not shown in the
    code provided.
    """

    # Query the user's income
    user_income = Income.query.filter_by(user_id=current_user.user_id).all()

    user_expenses = Expense.query.filter_by(user_id=current_user.user_id).all()
    # user_expenses = Expense.query.filter_by(user_id=1).all()

    user_budget = Budget.query.filter_by(user_id=current_user.user_id).all()
    # If the user hasn't made a budget yet
    if len(user_budget) == 0:
        # Query the database and add to the dictionary
        years = defaultdict(list)
        for i in range(len(user_expenses)):
            transaction = {}

            # mcc = user_expenses[i].mcc
            transaction['category'] = user_expenses[i].expense_category
            transaction['spent'] = float(user_expenses[i].expense_amount)
            transaction['budget'] = 0.0

            date = user_expenses[i].expense_date

            years[date[:7]].append(transaction)

        years_sorted = dict(sorted(years.items()))

        # Convert date to "Month Year"
        years = defaultdict(list)
        for key in years_sorted:
            date_obj = datetime.datetime.strptime(key, '%Y-%m')
            month_year = date_obj.strftime('%B %Y')
            years[month_year] = years_sorted[key]

        # Sum up the transactions in each month if theyre the same category
        for key, value_list in years.items():
            category_totals = {}
            for value in value_list:
                category = value['category']
                if category in category_totals:
                    category_totals[category]['spent'] += value['spent']
                    category_totals[category]['budget'] += value['budget']
                else:
                    category_totals[category] = {
                        'category': category,
                        'spent': value['spent'],
                        'budget': value['budget']
                    }
            years[key] = list(category_totals.values())
        print(years)

        months = list(years.keys())
        if len(months) == 0:
            return render_template('budget_summary_page.html')
        # print(list(months))
        # Let the user choose a month
        selected_month = request.args.get("months") or months[len(months)-1]
        # Query the database given the chosen month
        # Query to get the categories for the month and the spendings for each category

        spendings = years[selected_month]
        # List of categories
        categories = [list(i.values())[0] for i in spendings]
        # List of expenses for each category
        expenses = [list(i.values())[1] for i in spendings]
        # Total spendings for the month
        total = sum(expenses)
        # BREAKDOWN PIE PLOT
        cmap = plt.cm.get_cmap('PuRd', 10)
        # Create list of colors
        colors = [cmap(i) for i in range(10)]
        plt.subplots_adjust(left=0.2)
        plt.figure(figsize=(6, 4))
        wedgeprops = {'linewidth': 3, 'edgecolor': 'white'}
        wedges, texts, autotexts = plt.pie(expenses, colors=colors, startangle=90,
                                           counterclock=False, wedgeprops=wedgeprops, autopct='%1.1f%%', pctdistance=0.8, textprops=dict(fontsize=8))
        for i, autotext in enumerate(autotexts):
            angle = (wedges[i].theta2 - wedges[i].theta1) / \
                2.0 + wedges[i].theta1
            if angle < -120:
                angle -= 180
                autotext.set_rotation(angle)
            else:
                autotext.set_rotation(angle)
        plt.subplots_adjust(left=0.4)
        circle = plt.Circle((0, 0), 0.50, fc='white')
        fig = plt.gcf()
        fig.gca().add_artist(circle)
        plt.text(0, 0, f'Breakdown', fontsize=12, color='black',
                 ha='center', va='center', weight='bold')
        plt.axis('equal')
        # Add legend
        title_font = font_manager.FontProperties(weight='bold')
        plt.legend(wedges, categories, title_fontproperties=title_font,
                   loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), frameon=False)
        # Save the plot as a PNG image in memory
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        # Encode the image in base64 format for HTML display
        pie_plot_breakdown = base64.b64encode(buffer.getvalue()).decode()

        # THE TOTAL REMAINING DONUT PLOT
        total_remaining = sum([list(i.values())[2] for i in spendings])
        total_budget = sum(expenses)
        plt.figure(figsize=(6, 4))
        wedgeprops = {'linewidth': 3, 'edgecolor': 'white'}
        wedges, texts, autotexts = plt.pie([total_remaining, total_budget], colors=[
            '#5CB85C', '#D9534F'], startangle=90, counterclock=False, wedgeprops=wedgeprops, autopct='%1.1f%%', pctdistance=0.8, textprops=dict(fontsize=8))
        plt.subplots_adjust(left=0.4)
        circle = plt.Circle((0, 0), 0.50, fc='white')
        fig = plt.gcf()
        fig.gca().add_artist(circle)
        plt.text(0, 0, f'Total Remaining', fontsize=10, color='black',
                 ha='center', va='center', weight='bold')
        plt.axis('equal')
        # Add legend
        plt.legend(wedges, ['Total Remaining', 'Total Spent'],
                   loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), frameon=False)
        # Save the plot as a PNG image in memory
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        # Encode the image in base64 format for HTML display
        pie_plot_remaining = base64.b64encode(buffer.getvalue()).decode()

        total_spent_per_month = {month: sum(
            item['spent'] for item in data) for month, data in years.items()}

        # HISTORICAL BAR PLOT PYTHON
        cmap = plt.cm.get_cmap('PuRd', len(months))
        # Create list of colors
        colors = [cmap(i) for i in range(len(months))]
        plt.figure(figsize=(10, 6))
        plt.bar(months, list(total_spent_per_month.values()), color=colors)
        plt.xlabel("Months")
        plt.ylabel("Total Spent ($)")
        plt.xticks(rotation=90)
        # Save the plot as a PNG image in memory
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        # Encode the image in base64 format for HTML display
        bar_plot_months = base64.b64encode(buffer.getvalue()).decode()

        # category_month = request.form['Cats']
        # category_month= request.args.get("Cats")
        selected_category = request.args.get('Cats')

        monthly_spending_category = {month: sum(
            item['spent'] for item in data if item['category'] == selected_category) for month, data in years.items()}
        # print(years)
        colors = ['#e7e1ef', '#d4b9da', '#c994c7', '#df65b0', '#e7298a',
                  '#ce1256', '#980043', '#67001f', '#49000a', '#320003']
        bar_array = []
        x = list(monthly_spending_category.values())
        y = months
        for i in range(len(x)):
            bar_array.append([y[i], x[i], colors[i % 10]])

        user_income = Income.query.filter_by(
            user_id=current_user.user_id).all()
        years_income = defaultdict(list)
        total_income = 0.0
        for income in user_income:
            if income_month(income.income_date, selected_month):
                total_income += float(income.income_amount)

            income_statement = {}

            income_statement['income'] = float(user_income[i].income_amount)

            date = user_income[i].income_date

            years_income[date[:7]].append(income_statement)

        income_sorted = dict(sorted(years_income.items()))

        # Convert date to "Month Year"
        years_income = defaultdict(list)
        for key in income_sorted:
            date_obj = datetime.datetime.strptime(key, '%Y-%m')
            month_year = date_obj.strftime('%B %Y')
            years_income[month_year] = income_sorted[key]

        print(years_income)

        total_expenses = sum(expenses)
        total_remaining_income = total_income - total_expenses
        if total_remaining_income < 0.0:
            total_remaining_income = 0.0

        spendings = sorted(spendings, key=lambda x: (
            x['spent'], x['budget']), reverse=True)
        print(spendings)
        return render_template('budget_summary_page.html', user_income=user_income, months=months, selected_month=selected_month, total=total, spendings=spendings, pie_plot_breakdown=pie_plot_breakdown, pie_plot_remaining=pie_plot_remaining, bar_plot_months=bar_plot_months, bar_array=bar_array, selected_category=selected_category, total_remaining_income=total_remaining_income, total_expenses=total_expenses)

    # user_budget = Budget.query.filter_by(user_id=current_user.user_id).order_by(desc(Budget.date_start)).first()
    budget_month = user_budget[len(user_budget)-1].date_start[:7]
    budget_categories = [x.strip() for x in user_budget[len(
        user_budget)-1].categories.split(',')]
    budget_amounts = [float(x.strip())
                      for x in user_budget[len(user_budget)-1].amounts.split(',')]

    budget = defaultdict(list)
    for i in range(len(budget_categories)):
        budget_line = {}
        budget_line['category'] = budget_categories[i]
        budget_line['budget'] = budget_amounts[i]

        budget[user_budget[len(user_budget)-1].date_start[:7]
               ].append(budget_line)

    budget_sorted = {}
    for key in budget:
        date_obj = datetime.datetime.strptime(key, '%Y-%m')
        month_year = date_obj.strftime('%B %Y')
        budget_sorted[month_year] = budget[key]

    # Query the database and add to the dictionary
    years = defaultdict(list)
    for i in range(len(user_expenses)):
        transaction = {}

        # mcc = user_expenses[i].mcc
        transaction['category'] = user_expenses[i].expense_category
        transaction['spent'] = float(user_expenses[i].expense_amount)
        transaction['budget'] = 0.0

        date = user_expenses[i].expense_date

        years[date[:7]].append(transaction)

    years_sorted = dict(sorted(years.items()))

    # Convert date to "Month Year"
    years = defaultdict(list)
    for key in years_sorted:
        date_obj = datetime.datetime.strptime(key, '%Y-%m')
        month_year = date_obj.strftime('%B %Y')
        years[month_year] = years_sorted[key]

    # Sum up the transactions in each month if theyre the same category
    for key, value_list in years.items():
        category_totals = {}
        for value in value_list:
            category = value['category']
            if category in category_totals:
                category_totals[category]['spent'] += value['spent']
                category_totals[category]['budget'] += value['budget']
            else:
                category_totals[category] = {
                    'category': category,
                    'spent': value['spent'],
                    'budget': value['budget']
                }
        years[key] = list(category_totals.values())

    # Update the dict with all the budget values
    for key in list(years.keys()):
        # compare the months (right now only works with the latest month)
        if key == list(budget_sorted.keys())[0]:
            for item in budget_sorted[key]:
                category = item['category']
                budget_amount = item['budget']
                if not any(d.get('category') == category for d in years[key]):
                    years[key].append(
                        {'category': category, 'spent': 0.0, 'budget': budget_amount})
                else:
                    for d in years[key]:
                        if d.get('category') == category:
                            d['budget'] = budget_amount

    months = list(years.keys())
    if len(months) == 0:
        return render_template('budget_summary_page.html')
    # print(list(months))
    # Let the user choose a month
    selected_month = request.args.get("months") or months[len(months)-1]
    # Query the database given the chosen month
    # Query to get the categories for the month and the spendings for each category

    spendings = years[selected_month]
    # List of categories
    categories = [list(i.values())[0] for i in spendings]
    # List of expenses for each category
    expenses = [list(i.values())[1] for i in spendings]
    # Total spendings for the month
    total = sum(expenses)

    breakdown_cat = [entry['category']
                     for entry in spendings if entry['spent'] != 0.0]
    breakdown_spent = [entry['spent']
                       for entry in spendings if entry['spent'] != 0.0]

    # BREAKDOWN PIE PLOT
    cmap = plt.cm.get_cmap('PuRd', 10)
    # Create list of colors
    colors = [cmap(i) for i in range(10)]
    plt.subplots_adjust(left=0.2)
    plt.figure(figsize=(6, 4))
    wedgeprops = {'linewidth': 3, 'edgecolor': 'white'}
    wedges, texts, autotexts = plt.pie(breakdown_spent, colors=colors, startangle=90,
                                       counterclock=False, wedgeprops=wedgeprops, autopct='%1.1f%%', pctdistance=0.8, textprops=dict(fontsize=8))
    for i, autotext in enumerate(autotexts):
        angle = (wedges[i].theta2 - wedges[i].theta1)/2.0 + wedges[i].theta1
        if angle < -120:
            angle -= 180
            autotext.set_rotation(angle)
        else:
            autotext.set_rotation(angle)
    plt.subplots_adjust(left=0.4)
    circle = plt.Circle((0, 0), 0.50, fc='white')
    fig = plt.gcf()
    fig.gca().add_artist(circle)
    plt.text(0, 0, f'Breakdown', fontsize=12, color='black',
             ha='center', va='center', weight='bold')
    plt.axis('equal')
    # Add legend
    title_font = font_manager.FontProperties(weight='bold')
    plt.legend(wedges, breakdown_cat, title_fontproperties=title_font,
               loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), frameon=False)
    # Save the plot as a PNG image in memory
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    # Encode the image in base64 format for HTML display
    pie_plot_breakdown = base64.b64encode(buffer.getvalue()).decode()

    # THE TOTAL REMAINING DONUT PLOT
    total_remaining = sum([list(i.values())[2] for i in spendings])
    total_budget = sum(expenses)
    plt.figure(figsize=(6, 4))
    wedgeprops = {'linewidth': 3, 'edgecolor': 'white'}
    wedges, texts, autotexts = plt.pie([total_remaining, total_budget], colors=[
                                       '#5CB85C', '#D9534F'], startangle=90, counterclock=False, wedgeprops=wedgeprops, autopct='%1.1f%%', pctdistance=0.8, textprops=dict(fontsize=8))
    plt.subplots_adjust(left=0.4)
    circle = plt.Circle((0, 0), 0.50, fc='white')
    fig = plt.gcf()
    fig.gca().add_artist(circle)
    plt.text(0, 0, f'Total Remaining', fontsize=10, color='black',
             ha='center', va='center', weight='bold')
    plt.axis('equal')
    # Add legend
    plt.legend(wedges, ['Total Remaining', 'Total Spent'],
               loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), frameon=False)
    # Save the plot as a PNG image in memory
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    # Encode the image in base64 format for HTML display
    pie_plot_remaining = base64.b64encode(buffer.getvalue()).decode()

    total_spent_per_month = {month: sum(
        item['spent'] for item in data) for month, data in years.items()}
    # print(total_spent_per_month)

    # HISTORICAL BAR PLOT PYTHON
    cmap = plt.cm.get_cmap('PuRd', len(months))
    # Create list of colors
    colors = [cmap(i) for i in range(len(months))]
    plt.figure(figsize=(10, 6))
    plt.bar(months, list(total_spent_per_month.values()), color=colors)
    plt.xlabel("Months")
    plt.ylabel("Total Spent ($)")
    plt.xticks(rotation=90)
    # Save the plot as a PNG image in memory
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    # Encode the image in base64 format for HTML display
    bar_plot_months = base64.b64encode(buffer.getvalue()).decode()

    selected_category = request.args.get('Cats')
    # print(selected_category)

    monthly_spending_category = {month: sum(
        item['spent'] for item in data if item['category'] == selected_category) for month, data in years.items()}

    colors = ['#e7e1ef', '#d4b9da', '#c994c7', '#df65b0', '#e7298a',
              '#ce1256', '#980043', '#67001f', '#49000a', '#320003']
    bar_array = []
    x = list(monthly_spending_category.values())
    y = months
    for i in range(len(x)):
        bar_array.append([y[i], x[i], colors[i % 10]])

    user_income = Income.query.filter_by(user_id=current_user.user_id).all()
    years_income = defaultdict(list)
    total_income = 0.0
    for i in range(len(user_income)):
        total_income += float(user_income[i].income_amount)

        income_statement = {}

        # mcc = user_expenses[i].mcc
        income_statement['income'] = float(user_income[i].income_amount)

        date = user_income[i].income_date

        years_income[date[:7]].append(income_statement)

    income_sorted = dict(sorted(years_income.items()))

    # Convert date to "Month Year"
    years_income = defaultdict(list)
    for key in income_sorted:
        date_obj = datetime.datetime.strptime(key, '%Y-%m')
        month_year = date_obj.strftime('%B %Y')
        years_income[month_year] = income_sorted[key]

    print(years_income)

    total_income = 1
    total_expenses = sum(expenses)
    total_remaining_income = total_income - total_expenses
    if total_remaining_income < 0.0:
        total_remaining_income = 0.0

    spendings = sorted(spendings, key=lambda x: (
        x['spent'], x['budget']), reverse=True)
    return render_template('budget_summary_page.html', user_income=user_income, months=months, selected_month=selected_month, total=total, spendings=spendings, pie_plot_breakdown=pie_plot_breakdown, pie_plot_remaining=pie_plot_remaining, bar_plot_months=bar_plot_months, bar_array=bar_array, selected_category=selected_category, total_remaining_income=total_remaining_income, total_expenses=total_expenses)

# Filter to add $ and thousand comma to numbers


@views.app_template_filter()
def format_currency(value):
    """
    The function `format_currency` takes a numerical value and returns it formatted as a currency string
    with a dollar sign, commas for thousands separator, and two decimal places.

    :param value: a numerical value representing a currency amount
    :return: The function `format_currency` returns a string formatted as a currency with a dollar sign,
    comma separators for thousands, and two decimal places. The input value is first converted to a
    float before being formatted.
    """
    return "${:,.2f}".format(float(value))


@views.route('/profile', methods=['POST', 'GET'])
@login_required
def profile():
    """
    This function returns a rendered template of a user's profile page with their first name displayed.
    :return: a rendered HTML template called 'profile.html' with the first name of the current user
    passed as a parameter.
    """

    return render_template('profile.html', first_name=current_user.first_name)


@views.route('/budget_creator', methods=['POST', 'GET'])
@login_required
def budget_creator():
    """
    This function returns a rendered HTML template for a budget creator.
    :return: The function `budget_creator()` is returning a rendered HTML template called
    'budget_creator.html'.
    """
    shared_budgets = SharedBudget.query.filter_by(
        user_id=current_user.user_id).all()

    return render_template('budget_creator.html', shared_budgets=shared_budgets)

# FIXME: Insert the category and 0 into the budget db rather than leaving it blank


@views.route('/get_budget', methods=['POST', 'GET'])
@login_required
def get_budget():
    """
    This function takes in user input for budget categories and amounts, creates a pie chart of the
    budget breakdown, and returns a response with the pie chart and a message about whether the user's
    expenditure is above or below their income.
    :return: an HTTP response object containing an HTML string with a budget breakdown pie plot image
    encoded in base64 format. The HTML string also includes a message about whether the user's
    expenditure is below or above their income.
    """
    if request.method == "POST":
        budget = {'Income': request.form.get('income'), 'Eating Out': request.form.get('eating_out'),
                  'Entertainment': request.form.get('entertainment'), 'Groceries': request.form.get('groceries'),
                  'Transportation': request.form.get('transportation'),
                  'Health': request.form.get('health'), 'Shopping': request.form.get('shopping'), 'Donation': request.form.get('Donation'),
                  'Insurance': request.form.get('insurance'), 'Housing and Utilities': request.form.get('housing'), 'Services': request.form.get('services'),
                  'Education': request.form.get('education'), 'Miscellaneous': request.form.get('misc')}

        income = budget['Income']
        # Remove the 'income' category
        del budget['Income']
        # Convert to float
        budget = {key: float(value) for key, value in budget.items()}
        # Remove the categories that are equal to 0
        budget = {key: value for key, value in budget.items() if value > 0.0}

        # Insert into budget table
        budget_categories = ''
        for key in budget.keys():
            budget_categories += key + ', '
        budget_amounts = ''
        for key in budget.keys():
            budget_amounts += str(budget[key]) + ', '

        # FIXME: might have errors here
        # Delete previous budgets for the user and insert new budget into user's table
        existing_budgets = Budget.query.filter_by(
            user_id=current_user.user_id).all()
        for existing_budget in existing_budgets:
            db.session.delete(existing_budget)
        db.session.commit()

        today = date.today()
        new_budget = Budget(user_id=current_user.user_id,
                            categories=budget_categories[0:-2], amounts=budget_amounts[0:-2], date_start=today, duration="30 days")
        db.session.add(new_budget)
        db.session.commit()

        categories = list(budget.keys())
        totals = list(budget.values())

        # BUDGET BREAKDOWN PIE PLOT
        # Color scheme
        cmap = plt.cm.get_cmap('PuRd', 10)
        # Create list of colors
        colors = [cmap(i) for i in range(10)]
        colors.reverse()

        plt.subplots_adjust(left=0.2)
        plt.figure(figsize=(6, 4))
        wedgeprops = {'linewidth': 3, 'edgecolor': 'white'}
        wedges, texts, autotexts = plt.pie(totals, colors=colors, startangle=90,
                                           counterclock=False, autopct='%1.1f%%', wedgeprops=wedgeprops, pctdistance=0.8, textprops=dict(fontsize=8))
        for i, autotext in enumerate(autotexts):
            angle = (wedges[i].theta2 - wedges[i].theta1) / \
                2.0 + wedges[i].theta1
            if angle < -120:
                angle -= 180
                autotext.set_rotation(angle)
            else:
                autotext.set_rotation(angle)
        plt.subplots_adjust(left=0.4)
        title_font = font_manager.FontProperties(weight='bold')
        plt.legend(wedges, categories, title_fontproperties=title_font,
                   loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), frameon=False)
        # Save the plot as a PNG image in memory
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=200)
        buffer.seek(0)
        # Encode the image in base64 format for HTML display
        budget_pie = base64.b64encode(buffer.getvalue()).decode()

        # calculate whether income is higher than expenditure
        if float(income) >= sum([float(amount) for amount in budget.values()]) - float(income):
            # 'Your expenditure is below your income, well done!'
            html = f'<div style="text-align:center;"><h2 style="color: purple;">Your expenditure is below your income, well done!</h2>\n<h1 style="color: black;">Budget Breakdown</h1>\n<img src="data:image/jpeg;base64,{budget_pie}">'
            response = make_response(html)
            return response
        else:
            # "Your expenditure is above your income, consider reducing your spending."
            html = f'<div style="text-align:center;"><h2 style="color: purple;">Your expenditure is above your income, consider reducing your spending.</h2>\n<h1 style="color: black;">Budget Breakdown</h1>\n<img src="data:image/jpeg;base64,{budget_pie}">'
            response = make_response(html)
            return response


@views.route('/investment_tracking', methods=['POST', 'GET'])
@login_required
def investment_tracking():
    """
    This function tracks investments by adding new stocks to the database based on user input.
    :return: a rendered HTML template for the investment tracker page.
    """

    # data for stocks page form
    if request.method == "POST":
        amount = request.form["amount"]
        share = request.form["share"]
        symbol = request.form["shareSymbol"]
        date = request.form["orderDate"]

        new_stock = Stock_and_Crypto(ticker_name=share, ticker_symbol=symbol,
                                     total_price=amount, order_date=date, user_id=current_user.user_id, investment_type="Stock")
        db.session.add(new_stock)
        db.session.commit()
        return render_template('investment_tracker.html')

    return render_template('investment_tracker.html')


@views.route('/customInvest', methods=['POST', 'GET'])
@login_required
def customInvest():

    if request.method == "POST":
        amount = request.form["amount3"]
        name = request.form["desc"]
        date = request.form["orderDate3"]

        # new_stock2 = Stock_and_Crypto(ticker_name=name, ticker_symbol='',
        #                            total_price=amount, order_date=date, user_id=current_user.user_id, investment_type="Custom")

        new_custom_inv = Custom_Investment(
            user_id=current_user.user_id, purchased_amount=amount, sold_amount=0, purchased_date=date, sold_date=date, description=name)
        db.session.add(new_custom_inv)
        db.session.commit()

    return render_template('investment_tracker.html')


@views.route('/expenses', methods=['POST', 'GET'])
@login_required
def expenses():
    """
    This function filters and displays a user's expenses/transactions based on specified criteria such
    as price range, category, and account type.
    :return: a rendered HTML template with the filtered transactions, largest expense amount, minimum
    price, maximum price, and selected category.
    """

    price_min = request.args.get('price_min')
    price_max = request.args.get('price_max')
    category = request.args.get('category')
    account = request.args.get('account')

    # Query the user's expenses/transactions from the expenses table
    transactions = Expense.query.filter_by(
        user_id=current_user.user_id).all()

    largest = 0
    expense_count = 0
    for transaction in transactions:
        expense_count += 1
        if float(transaction.expense_amount) > largest:
            largest = float(transaction.expense_amount)

    filtered_transactions = []

    if not price_min or not price_max:
        filtered_transactions = transactions
        price_max = largest
        price_min = 0
    else:
        for transaction in transactions:
            if transaction.expense_amount >= float(price_min) and transaction.expense_amount <= float(price_max):
                if transaction.expense_category == category or not category:
                    if transaction.account_type.lower() == account.lower() or not account:
                        filtered_transactions.append(transaction)

    return render_template('expenses.html', transactions=filtered_transactions, largest=largest, price_min=price_min, price_max=price_max, category=category, expense_count=expense_count)


@views.route('/update_bill/<int:bill_id>', methods=['POST'])
@login_required
def update_bill(bill_id):
    """
    This function updates a bill object with new information provided in a form and saves it to a
    database.

    :param bill_id: The ID of the bill that needs to be updated
    :return: a redirect to the home page.
    """
    bill = Bill.query.get(bill_id)
    if bill is None:
        abort(404)

    # Check if custom days is a number
    try:
        float(request.form.get(
            'Custom_Freq', bill.bill_custom_freq))
    except ValueError:
        return redirect(url_for("views.home"))

    bill.bill_name = request.form.get('Name', bill.bill_name)
    bill.bill_description = request.form.get(
        'Description', bill.bill_description)
    bill.bill_due_date = request.form.get('Date', bill.bill_due_date)
    bill.bill_options = request.form.get('Frequency', bill.bill_options)

    # Only get custom days if the frequency is selected
    # TODO: Figure out a way to hide this input box
    if request.form.get('Frequency', bill.bill_options) == "Custom Days":
        bill.bill_custom_freq = request.form.get(
            'Custom_Freq', bill.bill_custom_freq)
    elif request.form.get('Frequency', bill.bill_options) != "Custom Days":
        bill.bill_custom_freq = -1

    db.session.commit()

    return redirect(url_for("views.home"))


@views.route('/update_bill_2/<int:bill_id>', methods=['POST'])
@login_required
def update_bill_2(bill_id):
    """
    This function updates a bill object with new information from a form and commits the changes to the
    database.

    :param bill_id: The ID of the bill that needs to be updated
    :return: a redirect to the "views.bills" route.
    """
    bill = Bill.query.get(bill_id)
    if bill is None:
        abort(404)

    # Check if custom days is a number
    try:
        float(request.form.get(
            'Custom_Freq', bill.bill_custom_freq))
    except ValueError:
        return redirect(url_for("views.bills"))

    bill.bill_name = request.form.get('Name', bill.bill_name)
    bill.bill_description = request.form.get(
        'Description', bill.bill_description)
    bill.bill_due_date = request.form.get('Date', bill.bill_due_date)
    bill.bill_options = request.form.get('Frequency', bill.bill_options)

    # Only get custom days if the frequency is selected
    # TODO: Figure out a way to hide this input box
    if request.form.get('Frequency', bill.bill_options) == "Custom Days":
        bill.bill_custom_freq = request.form.get(
            'Custom_Freq', bill.bill_custom_freq)
    elif request.form.get('Frequency', bill.bill_options) != "Custom Days":
        bill.bill_custom_freq = -1

    db.session.commit()

    return redirect(url_for("views.bills"))


@views.route('/update_expense/<int:expense_id>', methods=['POST'])
@login_required
def update_expense(expense_id):
    """
    This function updates an expense record in a database based on user input.

    :param expense_id: The ID of the expense that needs to be updated
    :return: a redirect to the "views.expenses" endpoint.
    """
    if not request.form:
        abort(400)
    expense = Expense.query.get(expense_id)
    if expense is None:
        abort(404)

    # Check if expense amount is a number
    try:
        float(request.form.get('Amount', expense.expense_amount))
    except ValueError:
        return redirect(url_for("views.expenses"))

    # Check if expense date is a valid date (YYYY-MM-DD)
    try:
        datetime.datetime.strptime(request.form.get(
            'Date', expense.expense_date), "%Y-%m-%d")
    except ValueError:
        return redirect(url_for("views.expenses"))

    expense.expense_amount = request.form.get('Amount', expense.expense_amount)
    expense.description = request.form.get('Description', expense.description)
    expense.expense_date = request.form.get('Date', expense.expense_date)
    expense.expense_category = request.form.get(
        'Category', expense.expense_category)
    expense.account_type = request.form.get('Account', expense.account_type)
    db.session.commit()
    return redirect(url_for("views.expenses"))


@views.route('/delete_expense/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    """
    This function deletes an expense from the database and redirects the user to the expenses page.

    :param expense_id: The ID of the expense that needs to be deleted from the database
    :return: a redirect to the "expenses" view.
    """

    expense = Expense.query.get(expense_id)
    if expense is None:
        abort(404)

    db.session.delete(expense)
    db.session.commit()

    return redirect(url_for("views.expenses"))


@views.route('/delete_bill/<int:bill_id>', methods=['POST'])
@login_required
def delete_bill(bill_id):
    """
    This function deletes a bill from the database and redirects the user to the home page.

    :param bill_id: The ID of the bill that needs to be deleted from the database
    :return: a redirect to the home page of the application.
    """

    bill = Bill.query.get(bill_id)
    if bill is None:
        abort(404)

    db.session.delete(bill)
    db.session.commit()

    return redirect(url_for("views.home"))


@views.route('/delete_bill_2/<int:bill_id>', methods=['POST'])
@login_required
def delete_bill_2(bill_id):
    """
    This function deletes a bill with a given ID from the database.

    :param bill_id: The ID of the bill that needs to be deleted from the database
    :return: a redirect to the "views.bills" endpoint.
    """

    bill = Bill.query.get(bill_id)
    if bill is None:
        abort(404)

    db.session.delete(bill)
    db.session.commit()

    return redirect(url_for("views.bills"))

# Function to create an ics calendar reminder for a bill


@views.route('/make_ics/<int:bill_id>', methods=['POST', 'GET'])
@login_required
def make_ics(bill_id):
    """
    The function "make_ics" takes a bill ID as input and performs some action(s) related to creating an
    ICS file. However, the specific actions performed are not clear from the given code snippet.

    :param bill_id: It seems like the function `make_ics` takes in a parameter `bill_id` which is likely
    a unique identifier for a bill or invoice. The function may use this identifier to generate an ICS
    (iCalendar) file for the bill, which can be used to schedule payment reminders or other
    """

    bill = Bill.query.get(bill_id)
    if bill is None:
        abort(404)

    # Create calendar and events
    c = Calendar()
    e = Event()
    e.name = bill.bill_name
    e.description = bill.bill_description
    e.begin = str(bill.bill_due_date)
    Event.make_all_day(e)
    c.events.add(e)
    c.events

    # Write the ics file with specified name, description and date
    path = f'website/Static/{bill.bill_name}.ics'
    with open(path, 'w') as my_file:
        my_file.writelines(c.serialize_iter())

    # Trigger browser download event
    download_path = f"Static\\{bill.bill_name}.ics"
    absolute_path = os.path.join(current_app.root_path, download_path)
    return send_file(absolute_path, as_attachment=True)


# Webpage to test category classification (for backend)


# Extract the model file
model_filename = os.path.join("website", "category_nlp.joblib")
current_path = os.getcwd()
file_path = os.path.join(current_path, model_filename)
if os.path.exists(file_path):
    model_data = joblib.load(file_path)
else:
    with zipfile.ZipFile(os.path.join(
            "website", "category_nlp.zip"), 'r') as zipf:
        zipf.extractall(os.path.join(current_path, "website"))

    # Load the saved model data from file
    model_data = joblib.load(file_path)


@views.route('/cat_class', methods=['POST', 'GET'])
def cat_class():
    """
    The function definition for a class called "cat_class" is provided, but there is no code inside the
    function.
    """
    if request.method == 'POST':

        # Retrieve the model and its associated functions
        model = model_data['model']
        tokenizer = model_data['tokenizer']
        index_to_labels = model_data['index_to_labels']

        # Get the user input description from the form
        input_description = request.form['description']

        # Make the prediction
        p = model.predict(np.expand_dims(get_sequences(
            tokenizer, [input_description])[0], axis=0))[0]
        pred_class = index_to_labels[np.argmax(p).astype('uint8')]

        # Render the template with the prediction result and user input
        return render_template('cat_class.html', prediction=pred_class, description=input_description)

    # Render the input form
    return render_template('cat_class.html')

# TEST PAGE
# @views.route('/test', methods=['POST', 'GET'])
# def test():
#     return render_template('test.html')

# Calculator PAGE


@views.route('/calc', methods=['POST', 'GET'])
@login_required
def calc():
    """
    The function "calc" is defined but its implementation is missing.
    """
    if request.method == 'POST':
        amount = float(request.form.get('amount'))
        duration = float(request.form.get('duration'))
        duration_unit = request.form.get('duration-unit')
        starting_balance = float(request.form.get('starting-balance'))
        interest_rate = float(request.form.get('interest-rate'))

        if amount and duration and duration_unit and interest_rate:
            if duration_unit == 'year':
                num_periods = duration * 12
            elif duration_unit == 'month':
                num_periods = duration
            elif duration_unit == 'week':
                num_periods = duration * 52

            target_amount = amount - starting_balance  # Adjusted target amount

            if starting_balance != 0:
                interest_rate_decimal = interest_rate / 100 / 12
                future_value = target_amount + starting_balance * \
                    (1 + interest_rate_decimal) ** num_periods
                cumulative_interest_earned = starting_balance * \
                    (interest_rate / 100) / 12 * num_periods
                monthly_savings = (
                    future_value - (starting_balance + cumulative_interest_earned)) / num_periods
            else:
                interest_rate_decimal = interest_rate / 100 / 12
                future_value = target_amount * \
                    (1 + interest_rate_decimal) ** num_periods
                cumulative_interest_earned = 0
                monthly_savings = (
                    future_value - cumulative_interest_earned) / num_periods

            fortnightly_savings = monthly_savings * 12 / 26
            weekly_savings = monthly_savings * 12 / 52

            # Prepare data for the chart
            chart_data = []
            cumulative_saved_amount = 0
            cumulative_interest_earned = 0
            current_balance = starting_balance

            if duration_unit == 'year':
                num_periods = int(duration)
                label_unit = 'Years'
            elif duration_unit == 'month':
                num_periods = int(duration)
                label_unit = 'Months'
            elif duration_unit == 'week':
                num_periods = int(duration) * 52
                label_unit = 'Weeks'
            else:
                num_periods = 0
                label_unit = ''

            for i in range(1, num_periods + 1):
                interest_earned = current_balance * (interest_rate / 100) / 12
                current_balance += monthly_savings + interest_earned
                cumulative_interest_earned += interest_earned
                cumulative_saved_amount += monthly_savings

                label = str(i) + ' ' + label_unit if label_unit else str(i)
                chart_data.append(
                    [label, cumulative_saved_amount, cumulative_interest_earned, starting_balance])

            return render_template('calc.html', monthly_savings=monthly_savings, amount=amount, duration=duration,
                                   duration_unit=duration_unit, starting_balance=starting_balance,
                                   interest_rate=interest_rate, chart_data=chart_data,
                                   fortnightly_savings=fortnightly_savings, weekly_savings=weekly_savings)

    duration_unit = 'Null'
    return render_template('calc.html', duration_unit=duration_unit)


# # Calculator borrowing_calculator
# @views.route('/borrowing_calculator', methods=['POST', 'GET'])
# def borrowing_calculator():
#     return render_template('borrowing_calculator.html')


def calculate_loan_repayment(principal, interest_rate, term, frequency):
    """
    This function calculates the loan repayment amount based on the principal, interest rate, term, and
    frequency of payments.

    :param principal: The amount of money borrowed or the initial amount of the loan
    :param interest_rate: The interest rate is the percentage charged by the lender for borrowing the
    principal amount. It is usually expressed as an annual percentage rate (APR) and is applied to the
    outstanding balance of the loan
    :param term: The term is the length of time over which the loan will be repaid. It is usually
    measured in years or months. For example, a 5-year loan has a term of 5 years
    :param frequency: Frequency refers to how often the loan payments are made. It can be specified in
    terms of months, weeks, or days. For example, if the frequency is set to "monthly", the loan
    payments will be made once a month. If the frequency is set to "weekly", the loan payments will
    """
    # Perform the calculation based on the provided parameters and return the results
    # You can implement your own calculation logic here
    # For demonstration purposes, let's assume a simple calculation:
    interest_rate /= 100  # Convert interest rate from percentage to decimal
    if frequency == 'monthly':
        num_periods = 12
    elif frequency == 'quarterly':
        num_periods = 4
    elif frequency == 'yearly':
        num_periods = 1
    elif frequency == 'weekly':
        num_periods = 52
    else:
        # Handle unsupported frequency option
        return None, None

    monthly_interest_rate = interest_rate / num_periods
    monthly_payment = (principal * monthly_interest_rate * (1 + monthly_interest_rate)
                       ** (term*num_periods)) / ((1 + monthly_interest_rate)**(term*num_periods) - 1)
    total_payment = monthly_payment * (num_periods * term)

    # PLOT
    # Generate x-axis values for the loan term
    x = range(0, (term*num_periods) + 1)

    # Generate y-axis values for the outstanding loan balance
    balance = principal
    y = [balance]

    for _ in range(0, (term*num_periods)):
        interest = balance * interest_rate / num_periods
        principal_payment = monthly_payment - interest
        balance -= principal_payment
        y.append(balance)

    rows = [[x[i], y[i]] for i in range(len(x))]
    return monthly_payment, total_payment, rows

# repayment_calculator PAGE


@views.route('/repayment_calculator', methods=['POST', 'GET'])
@login_required
def repayment_calculator():
    """
    The function name suggests that it is a repayment calculator, but without the code inside the
    function, it is impossible to provide a summary of what the function does.
    """
    if request.method == 'POST':
        principal = float(request.form['principal'])
        interest_rate = float(request.form['interest_rate'])
        term = int(request.form['term'])
        # New line to get the frequency option
        frequency = request.form['frequency']
        monthly_payment, total_payment, rows = calculate_loan_repayment(
            principal, interest_rate, term, frequency)

        return render_template('repayment_calculator.html', monthly_payment=monthly_payment, total_payment=total_payment, principal=principal, frequency=frequency, rows=rows)

    return render_template('repayment_calculator.html')


# stamp_duty_calculator PAGE
def calculate_stamp_duty(property_value, state):
    """
    This function calculates the stamp duty for a property in NSW based on its value and returns the
    result.

    :param property_value: The value of the property for which the stamp duty is being calculated
    :param state: The state in which the property is located. Currently, only NSW is implemented in the
    function
    :return: the stamp duty amount based on the property value and state. If the state is NSW, it
    calculates the stamp duty based on a tiered system with different rates for different property
    values. If the state is not NSW, the function does not currently have any code to calculate the
    stamp duty and will not return anything.
    """
    if state == 'NSW':
        if property_value <= 14000:
            return max(property_value * 0.0125, 10)
        elif property_value <= 32000:
            return ((property_value - 14000) * 0.015) + 175
        elif property_value <= 85000:
            return ((property_value - 32000) * 0.0175) + 445
        elif property_value <= 319000:
            return ((property_value - 85000) * 0.035) + 1372
        elif property_value <= 1064000:
            return ((property_value - 319000) * 0.045) + 9562
        else:
            return ((property_value - 1064000) * 0.055) + 43087
    elif state == 'VIC':
        if property_value <= 25000:
            return ((property_value * 0.014))
        elif property_value <= 130000:
            return ((property_value - 25000) * 0.024) + 350
        elif property_value <= 960000:
            return ((property_value - 130000) * 0.06) + 2870
        elif property_value <= 2000000:
            return ((property_value) * 0.055)
        else:
            return ((property_value - 2000000) * 0.065) + 110000
    elif state == 'QLD':
        if property_value <= 5000:
            return (0)
        elif property_value <= 75000:
            return ((property_value - 5000) * 0.015)
        elif property_value <= 540000:
            return ((property_value - 75000) * 0.035) + 1050
        elif property_value <= 1000000:
            return ((property_value - 540000) * 0.045) + 17325
        else:
            return ((property_value - 1000000) * 0.0575) + 38025


@views.route('/stamp_duty_calculator', methods=['POST', 'GET'])
@login_required
def stamp_duty_calculator():
    """
    There is no code in the function, so it is impossible to provide a summary.
    """
    if request.method == 'POST':
        property_value = float(request.form['property_value'])
        state = request.form.get('State')
        property_type = request.form.get('Type')
        stamp_duty = calculate_stamp_duty(property_value, state)
        if state == 'NSW':
            reg_mortgage = 154.00
            reg_transfer = 155.00
            discharge = 154.00
        elif state == 'VIC':
            reg_mortgage = 119.70
            discharge = 119.70
            reg_transfer = min((86.5 + (.00234 * property_value)), 3609)
        elif state == 'QLD':
            reg_mortgage = 195
            discharge = 195
            if property_value <= 180000:
                reg_transfer = 195
            elif property_value > 180000:
                excess_value = property_value - 180000
                additional_transfer = min(
                    (195 + (37/10000) * excess_value), (10000/180000) * excess_value)
                reg_transfer = 195 + additional_transfer

        return render_template('stamp_duty_calculator.html', stamp_duty=stamp_duty, reg_mortgage=reg_mortgage, discharge=discharge, reg_transfer=reg_transfer)
    return render_template('stamp_duty_calculator.html')


@views.route("/bills", methods=['POST', 'GET'])
@login_required
def bills():
    """
    Unfortunately, there is no code provided in the function, so it is impossible to provide a summary.
    """
    bill_count = 0
    user_bills = Bill.query.filter_by(
        user_id=current_user.user_id).all()

    # Update the due date if the date has passed
    for bill in user_bills:
        bill_count += 1
        while datetime.date.fromisoformat(str(bill.bill_due_date)) < datetime.date.today():
            # If the user has custom cycle, continuously add to the cycle to the past due date until the due date is in the future
            if bill.bill_options == "Custom Days":
                bill.bill_due_date = datetime.date.fromisoformat(str(bill.bill_due_date)) + datetime.timedelta(
                    days=bill.bill_custom_freq)
            # Else if the user has set day every month/quarter/6 months/year, add the month accordingly
            elif bill.bill_options == "Monthly":
                bill.bill_due_date = datetime.date.fromisoformat(
                    str(bill.bill_due_date)) + relativedelta(months=1)
            elif bill.bill_options == "Quarterly":
                bill.bill_due_date = datetime.date.fromisoformat(
                    str(bill.bill_due_date)) + relativedelta(months=3)
            elif bill.bill_options == "Biannual":
                bill.bill_due_date = datetime.date.fromisoformat(
                    str(bill.bill_due_date)) + relativedelta(months=6)
            elif bill.bill_options == "Annual":
                bill.bill_due_date = datetime.date.fromisoformat(
                    str(bill.bill_due_date)) + relativedelta(months=12)

        db.session.commit()

    return render_template("bills.html", user_bills=user_bills, bill_count=bill_count)

# Function to delete unused files from Static (e.g. csv and ics files)


def cleanup_static():
    static_path = current_app.static_folder
    files = os.listdir(static_path)
    for file in files:
        if file.endswith(".csv") or file.endswith(".ics"):
            os.remove(os.path.join(static_path, file))


@views.route('/goals', methods=['POST', 'GET'])
@login_required
def goals():

    goals = Goal.query.filter_by(
        user_id=current_user.user_id).all()
    goal_count = 0

    for goal in goals:
        goal_count += 1

    return render_template('goals.html', goals=goals, goal_count=goal_count)


@views.route('/update_goal/<int:goal_id>', methods=['POST'])
@login_required
def update_goal(goal_id):

    goal = Goal.query.get(goal_id)
    if goal is None:
        abort(404)

    # Check if goal amount is a number
    try:
        float(request.form.get(
            'Amount', goal.goal_amount))
    except ValueError:
        return redirect(url_for("views.goals"))

    # Check if updated goal date is in the past
    if datetime.datetime.today().date() > datetime.datetime.strptime(request.form.get('Date', goal.goal_date), "%Y-%m-%d").date():
        return redirect(url_for("views.goals"))

    # Check if goal amount is positive
    if Decimal(request.form.get('Amount', goal.goal_amount)) < 0:
        return redirect(url_for("views.goals"))

    # If the user shrinks the goal amount to be lower than total contribution, cap the contribution
    if goal.total_contribution > Decimal(request.form.get('Amount', goal.goal_amount)):
        goal.total_contribution = Decimal(
            request.form.get('Amount', goal.goal_amount))

    goal.goal_name = request.form.get('Name', goal.goal_name)
    goal.goal_description = request.form.get(
        'Description', goal.goal_description)
    goal.goal_amount = request.form.get('Amount', goal.goal_amount)
    goal.goal_date = request.form.get('Date', goal.goal_date)
    goal.contribution_frequency = request.form.get(
        'Frequency', goal.contribution_frequency)

    # TODO: update the cyclical freq when the user changes the goal target
    # Calculate the next contribution date and the amount
    if request.form.get(
            'Frequency', goal.contribution_frequency) == "Weekly":
        next_date = datetime.date.today() + relativedelta(days=7)
        delta = datetime.datetime.strptime(request.form.get(
            'Date', goal.goal_date), "%Y-%m-%d").date() - datetime.date.today()
        payments = delta.days / 7
        next_payment = float(request.form.get(
            'Amount', goal.goal_amount)) / payments

    elif request.form.get(
            'Frequency', goal.contribution_frequency) == "Fortnightly":
        next_date = datetime.date.today() + relativedelta(days=14)
        delta = datetime.datetime.strptime(request.form.get(
            'Date', goal.goal_date), "%Y-%m-%d").date() - datetime.date.today()
        payments = delta.days / 14
        next_payment = float(request.form.get(
            'Amount', goal.goal_amount)) / payments

    elif request.form.get(
            'Frequency', goal.contribution_frequency) == "Monthly":
        next_date = datetime.date.today() + relativedelta(months=1)
        delta = datetime.datetime.strptime(request.form.get(
            'Date', goal.goal_date), "%Y-%m-%d").date() - datetime.date.today()
        payment_per_day = float(request.form.get(
            'Amount', goal.goal_amount)) / delta.days
        next_payment = (next_date - datetime.date.today()
                        ).days * payment_per_day

    # if next contribution date is after the goal due date, set it as the goal due date.
    if next_date > datetime.datetime.strptime(request.form.get('Date', goal.goal_date), "%Y-%m-%d").date():
        next_date = request.form.get('Date', goal.goal_date)

    goal.cyclical_contribution = next_payment
    goal.next_contribution_amount = next_payment

    db.session.commit()

    return redirect(url_for("views.goals"))


@views.route('/delete_goal/<int:goal_id>', methods=['POST'])
@login_required
def delete_goal(goal_id):

    goal = Goal.query.get(goal_id)
    if goal is None:
        abort(404)

    history = ContributionHistory.query.filter_by(
        goal_id=goal_id).all()
    for entry in history:
        db.session.delete(entry)

    db.session.delete(goal)
    db.session.commit()

    return redirect(url_for("views.goals"))


@views.route('/goal_contribution/<int:goal_id>', methods=["POST", "GET"])
@login_required
def goal_contribution(goal_id):

    goal = Goal.query.get(goal_id)
    if goal is None:
        abort(404)

    # Check if custom days is a number
    try:
        float(request.form.get(
            'Contribution'))
    except ValueError:
        return redirect(url_for("views.goals"))

    contribution = request.form.get('Contribution')

    # Check if contribution amount if negative
    if Decimal(contribution) < 0:
        return redirect(url_for("views.goals"))

    # IF the user contributed same as their next payment amount, update the next payment amount
    if Decimal(contribution) == goal.next_contribution_amount:
        goal.next_contribution_amount = goal.cyclical_contribution

        if goal.contribution_frequency == "Weekly":
            goal.next_contribution_date = datetime.date.fromisoformat(
                str(goal.next_contribution_date)) + relativedelta(days=7)

        if goal.contribution_frequency == "Fortnightly":
            goal.next_contribution_date = datetime.date.fromisoformat(
                str(goal.next_contribution_date)) + relativedelta(days=14)

        if goal.contribution_frequency == "Monthly":
            goal.next_contribution_date = datetime.date.fromisoformat(
                str(goal.next_contribution_date)) + relativedelta(months=1)

        # Check if contribution overflowed over goal target
        if goal.total_contribution + Decimal(contribution) > goal.goal_amount:
            goal.total_contribution = goal.goal_amount
        else:
            goal.total_contribution += Decimal(contribution)

        # Check if next due date overflowed past goal target date, and set it to target date if so.
        if datetime.date.fromisoformat(str(goal.next_contribution_date)) > datetime.date.fromisoformat(str(goal.goal_date)):
            goal.next_contribution_date = datetime.date.fromisoformat(
                str(goal.goal_date))

        # Check if remaining payment is lower than next payment, and set next payment to remainder if so
        remainder = goal.goal_amount - goal.total_contribution
        if remainder < goal.next_contribution_amount:
            goal.next_contribution_amount = remainder

        # Insert a new contribution history in the table
        new_history = ContributionHistory(
            goal_id=goal_id, amount=contribution, timestamp=datetime.datetime.now())
        db.session.add(new_history)

        db.session.commit()

        return redirect(url_for("views.goals"))

    # IF the user contributed less than their next payment amount, update the next payment amount
    if Decimal(contribution) < goal.next_contribution_amount:
        goal.next_contribution_amount -= Decimal(contribution)
        db.session.commit()

        # Check if contribution overflowed over goal target
        if goal.total_contribution + Decimal(contribution) > goal.goal_amount:
            goal.total_contribution = goal.goal_amount
        else:
            goal.total_contribution += Decimal(contribution)

        db.session.commit()

        # Check if remaining payment is lower than next payment, and set next payment to remainder if so
        remainder = goal.goal_amount - goal.total_contribution
        if remainder < goal.next_contribution_amount:
            goal.next_contribution_amount = remainder

        # Insert a new contribution history in the table
        new_history = ContributionHistory(
            goal_id=goal_id, amount=contribution, timestamp=datetime.datetime.now())
        db.session.add(new_history)

        return redirect(url_for("views.goals"))

    # If the user contributed more than their next payment amount, update the next payment date/amount accordingly
    if Decimal(contribution) > goal.next_contribution_amount:
        if goal.contribution_frequency == "Weekly":

            overflow = Decimal(contribution) - goal.next_contribution_amount
            next_date = datetime.date.fromisoformat(
                str(goal.next_contribution_date))

            while overflow > 0:
                next_date = next_date + relativedelta(days=7)

                if overflow < goal.next_contribution_amount:
                    next_payment = goal.cyclical_contribution - overflow
                    overflow = 0
                elif overflow == goal.next_contribution_amount:
                    next_payment = goal.cyclical_contribution
                    overflow = 0
                elif overflow > goal.next_contribution_amount:
                    overflow -= goal.next_contribution_amount

            goal.next_contribution_date = next_date
            goal.next_contribution_amount = next_payment
            db.session.commit()

        elif goal.contribution_frequency == "Fortnightly":
            overflow = Decimal(contribution) - goal.next_contribution_amount
            next_date = datetime.date.fromisoformat(
                str(goal.next_contribution_date))

            while overflow > 0:
                next_date = next_date + relativedelta(days=14)
                if overflow < goal.next_contribution_amount:
                    next_payment = goal.next_contribution_amount - overflow
                    overflow = 0
                elif overflow == goal.next_contribution_amount:
                    next_payment = goal.cyclical_contribution
                    overflow = 0
                elif overflow > goal.next_contribution_amount:
                    overflow -= goal.next_contribution_amount

            if overflow < 0:
                next_payment -= overflow

            goal.next_contribution_date = next_date
            goal.next_contribution_amount = next_payment
            db.session.commit()

        elif goal.contribution_frequency == "Monthly":
            overflow = Decimal(contribution) - goal.next_contribution_amount
            next_date = datetime.date.fromisoformat(
                str(goal.next_contribution_date))

            while overflow > 0:
                next_date = next_date + relativedelta(months=1)
                if overflow < goal.next_contribution_amount:
                    next_payment = goal.next_contribution_amount - overflow
                    overflow = 0
                elif overflow == goal.next_contribution_amount:
                    next_payment = goal.cyclical_contribution
                    overflow = 0
                elif overflow > goal.next_contribution_amount:
                    overflow -= goal.next_contribution_amount

            if overflow < 0:
                next_payment -= Decimal(contribution)

            goal.next_contribution_date = next_date
            goal.next_contribution_amount = next_payment
            db.session.commit()

        # Check if contribution overflowed over goal target
        if goal.total_contribution + Decimal(contribution) > goal.goal_amount:
            goal.total_contribution = goal.goal_amount
        else:
            goal.total_contribution += Decimal(contribution)

        # Check if next due date overflowed past goal target date, and set it to target date if so.
        if datetime.date.fromisoformat(str(goal.next_contribution_date)) > datetime.date.fromisoformat(str(goal.goal_date)):
            goal.next_contribution_date = datetime.date.fromisoformat(
                str(goal.goal_date))

        # Check if remaining payment is lower than next payment, and set next payment to remainder if so
        remainder = goal.goal_amount - goal.total_contribution
        if remainder < goal.next_contribution_amount:
            goal.next_contribution_amount = remainder

        # Insert a new contribution history in the table
        new_history = ContributionHistory(
            goal_id=goal_id, amount=contribution, timestamp=datetime.datetime.now())
        db.session.add(new_history)

        db.session.commit()

        return redirect(url_for("views.goals"))

    # Check if contribution overflowed over goal target
    if goal.total_contribution + Decimal(contribution) > goal.goal_amount:
        goal.total_contribution = goal.goal_amount
    else:
        goal.total_contribution += Decimal(contribution)

    # Insert a new contribution history in the table
    new_history = ContributionHistory(
        goal_id=goal_id, amount=contribution, timestamp=datetime.datetime.now())
    db.session.add(new_history)

    db.session.commit()

    return redirect(url_for("views.goals"))


def top_expenses():
    # Find the user's top expenses and give them a recommendation to cut down
    expenses = Expense.query.filter_by(
        user_id=current_user.user_id).all()

    year = datetime.datetime.now().year
    month = datetime.datetime.now().month

    # Get the first word from each description and add the amount per word
    word_count = {}
    for expense in expenses:
        if int((expense.expense_date).split('-')[0]) == year and int((expense.expense_date).split('-')[1]) == month:
            first_word = expense.description.split(' ')[0]
            if first_word not in word_count.keys():
                word_count[first_word] = [
                    1, expense.expense_amount, [expense.expense_category]]
            else:
                word_count[first_word][0] += 1
                word_count[first_word][1] += expense.expense_amount
                word_count[first_word][2].append(expense.expense_category)

    # Filter out entries that only have a count of 1
    word_count = {key: value for key,
                  value in word_count.items() if value[0] != 1}

    # Get the top 5 words that have the highest spending
    sorted_dict = dict(
        sorted(word_count.items(), key=lambda x: x[1][1], reverse=True))

    # Count the categories of the dict
    for key in sorted_dict.keys():
        counter = Counter(sorted_dict[key][2])
        most_common_category = counter.most_common(1)[0][0]
        sorted_dict[key][2] = most_common_category

    # if the sorted dict doesn't have 5 items, return the whole dict
    if len(sorted_dict) < 5:
        return sorted_dict

    # Else return top 5
    top_five = list(sorted_dict.items())[:5]
    dict_top_five = dict(top_five)
    return dict_top_five


@views.route('/budget_sharing', methods=['POST', 'GET'])
def budget_sharing():

    # Query the shared budget table and display all budgets the current user has received

    shared_budgets = SharedBudget.query.filter_by(
        user_id=current_user.user_id).all()

    # User can send a budget to another user via their email
    sharing_form = BudgetSharingForm()
    if sharing_form.validate_on_submit():

        # Ensure that the user don't put in their email
        if sharing_form.email.data.lower() == current_user.email:
            flash(
                "You can't share a budget with yourself. Please enter another user's email.")
            return render_template('budget_sharing.html', sharing_form=sharing_form, shared_budgets=shared_budgets)

        # Query the db for an email that matches the input
        receiver = User.query.filter_by(
            email=sharing_form.email.data.lower()).first()

        if not receiver:
            flash("This user does not exist.")
            return render_template('budget_sharing.html', sharing_form=sharing_form, shared_budgets=shared_budgets)

        # Insert a new shared budget into Shared Budget Table
        current_budget = Budget.query.filter_by(
            user_id=current_user.user_id).first()

        # Let the user know if they don't have a budget created
        if not current_budget:
            flash("You haven't created a budget yet.")
            return render_template('budget_sharing.html', sharing_form=sharing_form, shared_budgets=shared_budgets)

        sender_full_name = f"{current_user.first_name} {current_user.last_name}"
        new_shared = SharedBudget(user_id=receiver.user_id, sender_id=current_user.user_id, sender_name=sender_full_name,
                                  categories=current_budget.categories, amounts=current_budget.amounts,
                                  date_start=current_budget.date_start, duration=current_budget.duration)
        db.session.add(new_shared)
        db.session.commit()

        flash("Budget sent.")

        return render_template('budget_sharing.html', sharing_form=sharing_form, shared_budgets=shared_budgets)

    return render_template('budget_sharing.html', sharing_form=sharing_form, shared_budgets=shared_budgets)


@views.app_template_global()
def my_zip(categories, amounts):
    # Custom zip () function to pass onto jinja html
    categories = categories.split(',')
    amounts = amounts.split(',')
    return zip(categories, amounts)


@views.route('/delete_shared_budget/<int:shared_budget_id>', methods=['POST'])
@login_required
def delete_shared_budget(shared_budget_id):

    shared_budget = SharedBudget.query.get(shared_budget_id)
    if shared_budget is None:
        abort(404)

    db.session.delete(shared_budget)
    db.session.commit()

    return redirect(url_for("views.budget_sharing"))


@views.route('/import_budget/<int:shared_budget_id>', methods=['POST'])
@login_required
def import_budget(shared_budget_id):

    shared_budget = SharedBudget.query.get(shared_budget_id)
    if shared_budget is None:
        abort(404)

    target_budget = Budget.query.filter_by(
        user_id=current_user.user_id).first()
    if target_budget:
        db.session.delete(target_budget)

    new_budget = Budget(user_id=current_user.user_id, categories=shared_budget.categories,
                        amounts=shared_budget.amounts, date_start=shared_budget.date_start,
                        duration=shared_budget.duration)
    db.session.add(new_budget)

    db.session.commit()

    flash("Import Budget Successful")

    return redirect(url_for("views.budget_sharing"))


@views.route('/delete_income/<int:income_id>', methods=['POST'])
@login_required
def delete_income(income_id):

    income = Income.query.get(income_id)
    if income is None:
        abort(404)

    db.session.delete(income)
    db.session.commit()

    return redirect(url_for("uploads.income"))


@views.route('/update_income/<int:income_id>', methods=['POST'])
@login_required
def update_income(income_id):

    if not request.form:
        abort(400)
    income = Income.query.get(income_id)
    if income is None:
        abort(404)

    # Check if income amount is a number
    try:
        float(request.form.get('Amount', income.income_amount))
    except ValueError:
        return redirect(url_for("uploads.income"))

    # Check if income date is a valid date (YYYY-MM-DD)
    try:
        datetime.datetime.strptime(request.form.get(
            'Date', income.income_date), "%Y-%m-%d")
    except ValueError:
        return redirect(url_for("uploads.income"))

    income.income_amount = request.form.get('Amount', income.income_amount)
    income.income_description = request.form.get(
        'Description', income.income_description)
    income.income_date = request.form.get('Date', income.income_date)
    income.account_type = request.form.get('Account', income.account_type)
    db.session.commit()
    return redirect(url_for("uploads.income"))


@views.app_template_global()
def income_month(income_date, selected_month):
    # Checks if income_date matches selected_month
    return income_date.split('-')[0] == selected_month.split(' ')[1] and \
        calendar.month_name[int(income_date.split('-')[1])
                            ] == selected_month.split(' ')[0]


# TEST PAGE
# @views.route('/test', methods=['POST', 'GET'])
# def test():
#     return render_template('test.html')


# Faq Pages

@views.route('/FAQ', methods=['POST', 'GET'])
def FAQ():
    return render_template('FAQ.html')


@views.route('/FAQDashboard', methods=['POST', 'GET'])
def FAQDashboard():
    return render_template('FAQDashboard.html')


@views.route('/FAQ_Budget_Creator', methods=['POST', 'GET'])
def FAQ_Budget_Creator():
    return render_template('FAQ_Budget_Creator.html')


@views.route('/FAQ_Budget_Summary', methods=['POST', 'GET'])
def FAQ_Budget_Summary():
    return render_template('FAQ_Budget_Summary.html')


@views.route('/FAQ_Expenses', methods=['POST', 'GET'])
def FAQ_Expenses():
    return render_template('FAQ_Expenses.html')


@views.route('/FAQ_Investment', methods=['POST', 'GET'])
def FAQ_Investment():
    return render_template('FAQ_Investment.html')


@views.route('/FAQ_Calc', methods=['POST', 'GET'])
def FAQ_Calc():
    return render_template('FAQ_Calc.html')


@views.route('/FAQ_Bills', methods=['POST', 'GET'])
def FAQ_Bills():
    return render_template('FAQ_Bills.html')


@views.route('/FAQ_Goals', methods=['POST', 'GET'])
def FAQ_Goals():
    return render_template('FAQ_Goals.html')


@views.route('/FAQ_Profile', methods=['POST', 'GET'])
def FAQ_Profile():
    return render_template('FAQ_Profile.html')


@views.app_template_global()
def rand_profit_loss(stock_and_crypto_id):
    multiplier = uniform(0.9, 1.1)
    total_price = Stock_and_Crypto.query.get(stock_and_crypto_id).total_price
    dummy_price = round(Decimal(multiplier) * total_price, 2)

    return dummy_price
    # multiplier = uniform(0.9, 1.1)
    # total_price = Stock_and_Crypto.query.get(stock_and_crypto_id).total_price
    # dummy_price = Decimal(multiplier) * total_price

    # # 100, 50

    # if dummy_price > total_price:
    #     #make green %
    #     return round(dummy_price / total_price * 100 - 100, 2)
    #     #return "+" + str(round(dummy_price / total_price * 100 - 100, 2)) + "%"

    # else:
    #     #make red %
    #     return round(100 - dummy_price / total_price * 100, 2)
    #     #return "-" + str(100 - round(dummy_price / total_price * 100, 2)) + "%"


@views.app_template_global()
def contribution_history(id):
    history = ContributionHistory.query.filter_by(
        goal_id=id).order_by(ContributionHistory.timestamp).all()
    return history


@views.route('/goal_ics/<int:goal_id>', methods=['POST', 'GET'])
@login_required
def goal_ics(goal_id):

    goal = Goal.query.get(goal_id)
    if goal is None:
        abort(404)

    # Create calendar and events
    c = Calendar()
    e = Event()
    e.name = f"Upcoming reminder for {goal.goal_name}"
    e.description = f"Goal: {goal.goal_name}\nDescription: {goal.goal_description}\n${goal.next_contribution_amount} due on {goal.next_contribution_date}"
    e.begin = str(goal.next_contribution_date)
    Event.make_all_day(e)
    c.events.add(e)
    c.events

    # Write the ics file with specified name, description and date
    path = f'website/Static/{goal.goal_name}.ics'
    with open(path, 'w') as my_file:
        my_file.writelines(c.serialize_iter())

    # Trigger browser download event
    download_path = f"Static\\{goal.goal_name}.ics"
    absolute_path = os.path.join(current_app.root_path, download_path)
    return send_file(absolute_path, as_attachment=True)
