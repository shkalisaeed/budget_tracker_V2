# Database code goes in here

from flask_login import UserMixin

from . import db

# FIXME: If the tables don't work add UserMixin back


class User(UserMixin, db.Model):

    __tablename__ = 'user'

    # Getter function to overide login_manager's get_id func
    def get_id(self):
        """
        This function returns the user ID.
        :return: The method `get_id` is returning the `user_id` attribute of the object.
        """
        return (self.user_id)

    user_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    dob = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(), unique=True)
    password = db.Column(db.String(80))
    date_created = db.Column(db.String(20), nullable=False)
    attempts = db.Column(db.Integer, default=0)
    lock_start = db.Column(db.String(), default='')
    lock_end = db.Column(db.String(), default='')

    # Link with Account and Budget
    # account = db.relationship("Account", backref="user")
    budget = db.relationship("Budget", backref="user")

    # Constructor
    def __init__(self, first_name, last_name, dob, email, password, date_created):
        self.first_name = first_name
        self.last_name = last_name
        self.dob = dob
        self.email = email
        self.password = password
        self.date_created = date_created


class Expense(db.Model):

    __tablename__ = 'expense'

    expense_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'user.user_id'), nullable=False)
    expense_amount = db.Column(db.Numeric(
        precision=10, scale=2), nullable=False)
    description = db.Column(db.String(), nullable=False)
    expense_date = db.Column(db.String(20), nullable=False)
    expense_category = db.Column(db.String(), nullable=False)
    account_type = db.Column(db.String(), nullable=False)

    # Constructor
    def __init__(self, user_id, expense_amount, description, expense_date, expense_category, account_type):
        self.user_id = user_id
        self.expense_amount = expense_amount
        self.description = description
        self.expense_date = expense_date
        self.expense_category = expense_category
        self.account_type = account_type

# Class to store user created budgets


class Budget(db.Model):

    __tablename__ = 'budget'

    budget_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'user.user_id'), nullable=False)
    categories = db.Column(db.String, nullable=False)
    amounts = db.Column(db.String, nullable=False)
    date_start = db.Column(db.String(20), nullable=False)
    duration = db.Column(db.String(20), nullable=False)

    # Constructor
    def __init__(self, user_id, categories, amounts, date_start, duration):
        self.user_id = user_id
        self.categories = categories
        self.amounts = amounts
        self.date_start = date_start
        self.duration = duration

class Stock_and_Crypto(db.Model):

    __tablename__ = 'stock_and_crypto'

    stock_and_crypto_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'user.user_id'), nullable=False)
    # investment_id = db.Column(db.Integer, db.ForeignKey(
    #     'investment.investment_id'), nullable=False)
    ticker_name = db.Column(db.String(50), nullable=False)
    ticker_symbol = db.Column(db.String(50), nullable=False)
    # quantity = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    total_price = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    # unit_price = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    order_date = db.Column(db.String(20), nullable=False)
    # fulfillment_date = db.Column(db.String(20), nullable=False)
    investment_type = db.Column(db.String(50), nullable=False)

    # Constructor
    def __init__(self, ticker_name, ticker_symbol, total_price, order_date, user_id, investment_type):
        # self.investment_id = investment_id
        self.ticker_name = ticker_name
        self.ticker_symbol = ticker_symbol
        # self.quantity = quantity
        self.total_price = total_price
        # self.unit_price = unit_price
        self.order_date = order_date
        # self.fulfillment_date = fulfillment_date
        self.user_id = user_id
        self.investment_type = investment_type


class Custom_Investment(db.Model):

    __tablename__ = 'custom_investment'

    custom_investment_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'user.user_id'), nullable=False)
    # investment_id = db.Column(db.Integer, db.ForeignKey(
    #     'investment.investment_id'), nullable=False)
    description = db.Column(db.String(100), nullable=True)
    purchased_amount = db.Column(db.Numeric(
        precision=10, scale=2), nullable=False)
    sold_amount = db.Column(db.Numeric(precision=10, scale=2), nullable=True)
    purchased_date = db.Column(db.String(20), nullable=False)
    sold_date = db.Column(db.String(20), nullable=False)

    # Constructor
    def __init__(self, user_id, description, purchased_amount, sold_amount, purchased_date, sold_date):
        self.user_id = user_id
        self.description = description
        self.purchased_amount = purchased_amount
        self.sold_amount = sold_amount
        self.purchased_date = purchased_date
        self.sold_date = sold_date


class Bill(db.Model):

    __tablename__ = "bill"

    bill_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'user.user_id'), nullable=False)
    bill_name = db.Column(db.String(50), nullable=False)
    # bill_amount = db.Column(db.Numeric(precision=10, scale=2), nullable=True)
    bill_description = db.Column(db.String(100))
    bill_due_date = db.Column(db.String(20), nullable=False)
    bill_options = db.Column(db.String(20), nullable=False)
    bill_custom_freq = db.Column(db.Integer)
    # cycle_period - either fixed day of month or every x days
    # date sanitisatuin yyyy-mm-dd

    # Constructor
    def __init__(self, user_id, bill_name, bill_description, bill_due_date, bill_options, bill_custom_freq):
        self.user_id = user_id
        self.bill_name = bill_name
        self.bill_description = bill_description
        self.bill_due_date = bill_due_date
        self.bill_options = bill_options
        self.bill_custom_freq = bill_custom_freq


class Goal(db.Model):

    __tablename__ = "goal"

    goal_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'user.user_id'), nullable=False)
    goal_name = db.Column(db.String(50), nullable=False)
    goal_amount = db.Column(db.Numeric(precision=10, scale=2), nullable=True)
    goal_description = db.Column(db.String(100))
    goal_date = db.Column(db.String(20), nullable=False)
    total_contribution = db.Column(db.Numeric(
        precision=10, scale=2), nullable=True)
    contribution_frequency = db.Column(db.String(20), nullable=False)
    cyclical_contribution = db.Column(db.Numeric(
        precision=10, scale=2), nullable=True)
    next_contribution_date = db.Column(db.String(20), nullable=True)
    next_contribution_amount = db.Column(db.Numeric(
        precision=10, scale=2), nullable=True)

    # Constructor
    def __init__(self, user_id, goal_name, goal_amount, goal_description, goal_date,
                 contribution_frequency, next_contribution_date, next_contribution_amount, cyclical_contribution):
        self.user_id = user_id
        self.goal_name = goal_name
        self.goal_amount = goal_amount
        self.goal_description = goal_description
        self.goal_date = goal_date
        self.total_contribution = 0
        self.contribution_frequency = contribution_frequency
        self.next_contribution_date = next_contribution_date
        self.next_contribution_amount = next_contribution_amount
        self.cyclical_contribution = cyclical_contribution


class SharedBudget(db.Model):

    __tablename__ = "shared_budget"

    shared_budget_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'user.user_id'), nullable=False)
    sender_id = db.Column(db.Integer, nullable=False)
    sender_name = db.Column(db.String, nullable=False)
    categories = db.Column(db.String, nullable=False)
    amounts = db.Column(db.String, nullable=False)
    date_start = db.Column(db.String(20), nullable=False)
    duration = db.Column(db.String(20), nullable=False)

    # Constructor
    def __init__(self, user_id, sender_id, sender_name, categories, amounts, date_start, duration):
        self.user_id = user_id
        self.sender_id = sender_id
        self.sender_name = sender_name
        self.categories = categories
        self.amounts = amounts
        self.date_start = date_start
        self.duration = duration


class Income(db.Model):

    __tablename__ = "income"

    income_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'user.user_id'), nullable=False)
    income_amount = db.Column(db.Numeric(
        precision=10, scale=2), nullable=False)
    income_description = db.Column(db.String(), nullable=False)
    income_date = db.Column(db.String(20), nullable=False)
    account_type = db.Column(db.String(), nullable=False)

    # Constructor
    def __init__(self, user_id, income_amount, income_description, income_date, account_type):
        self.user_id = user_id
        self.income_amount = income_amount
        self.income_description = income_description
        self.income_date = income_date
        self.account_type = account_type


class ContributionHistory(db.Model):

    __tablename__ = "contribution_history"

    history_id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, db.ForeignKey(
        'goal.goal_id'), nullable=False)
    amount = db.Column(db.Numeric(
        precision=10, scale=2), nullable=False)
    timestamp = db.Column(db.String(), nullable=False)

    # Constructor
    def __init__(self, goal_id, amount, timestamp):
        self.goal_id = goal_id
        self.amount = amount
        self.timestamp = timestamp
