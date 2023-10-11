import string
from datetime import date, timedelta
from random import choice, randint, uniform, sample
from dateutil.relativedelta import relativedelta
from werkzeug.security import generate_password_hash

from . import db
from .models import User, Expense, Budget, Stock_and_Crypto, Custom_Investment, Bill, Goal


def initialise_db_contents():
    """
    This function initializes the contents of the database, populating it with
    some dummy data
    """
    add_user_data()
    add_expense_data()
    add_budget_data()
    add_bill_data()
    add_goal_data()
    add_custom_investment_data()
    add_stock_and_crypto_data()


def add_user_data():
    """
    This function generates a specified number of users
    """
    first_names = ["Alice", "Bob", "Emma", "Grace", "Harry", "John", "Jane", "Jack", "Charlotte",
                   "Lucas", "Amelia", "Mason", "Oliver", "Evelyn", "Jill", "Sara", "James", "Ali", "Sam", "Ethan"]
    last_names = ["Adam", "Davis", "Fisher", "Harris", "Lee", "Rodriguez", "Doe", "Reed", "Smith", "Brown",
                  "Johnson", "Jones", "Cooper", "Mitchel", "Wilson", "Flores", "Hall", "Irving", "Green", "Miller"]
    # ensure users are at least 18
    min_age = date.today() - timedelta(days=365 * 18)
    emailopt = ["@gmail.com", "@example.com",
                "@yahoo.com", "@hotmail.com",
                "@outlook.com", "@notascam.com", "@tempmail.com"]
    characters = string.ascii_letters + string.digits + string.punctuation

    # Generate 10 rows of user data
    for i in range(10):
        first_name = choice(first_names)
        last_name = choice(last_names)
        # results in ~50 years max, change to str format
        dob = str(min_age - timedelta(days=randint(1, 12000)))
        email = (first_name + "." + last_name + choice(emailopt)).lower()
        # randomise password between 8 and 16 characters, and hash it
        password = "password123"
        hash_pswd = generate_password_hash(password, method="sha256")
        # randomise account creation dates as last 2 years
        date_created = str(date.today() - timedelta(days=randint(1, 730)))

        new_user = User(first_name=first_name, last_name=last_name, dob=dob,
                        email=email, password=hash_pswd, date_created=date_created)
        db.session.add(new_user)
    db.session.commit()
    generate_user_list()


def generate_user_list():
    """
    This function generates a list of distinct user IDs from a database.
    :return: The function `generate_user_list()` returns a list of unique user IDs from the `User` table
    in the database.
    """
    users = []
    for user in db.session.query(User.user_id).distinct():
        users.append(user[0])
    return users


def add_expense_data():
    """
    This function generates 50 random expenses for existing users with various categories and account
    types.
    """
    # make 50 expenses over the existing users
    user_ids = generate_user_list()
    expense_categories = ["Donation", "Eating out", "Education", "Entertainment", "Groceries", "Health",
                          "Housing & Utilities", "Insurance", "Services", "Shopping",
                          "Travel and Transportation", "Miscellaneous & Other Expenses"]
    account_types = ["debit", "credit", "other"]
    for i in range(100):
        user_id = choice(user_ids)
        expense_amount = round(uniform(0.01, 250.00), 2)
        expense_date = str(date.today() - timedelta(days=randint(1, 5)))
        expense_category = choice(expense_categories)

        if expense_category == "Donation":
            description = choice(["Direct-Debit", "One-Off"])
        elif expense_category == "Eating out":
            description = choice(["KFC", "McDonalds", "Starbucks"])
        elif expense_category == "Education":
            description = choice(["Tuition", "Supplies", "Courses"])
        elif expense_category == "Entertainment":
            description = choice(["iMAX", "GoodGames", "Arcade"])
        elif expense_category == "Groceries":
            description = choice(["Woolworths", "Coles", "Aldi"])
        elif expense_category == "Health":
            description = choice(["Gym", "Vitamins", "Medicine"])
        elif expense_category == "Housing & Utilities":
            description = choice(["Bills", "Other", "Rent"])
        elif expense_category == "Insurance":
            description = choice(["Home", "Car", "Health"])
        elif expense_category == "Services":
            description = choice(["Childcare", "Lawyer"])
        elif expense_category == "Shopping":
            description = choice(["Kathmandu", "Kmart", "Myers"])
        elif expense_category == "Travel and Transport":
            description = choice(["Bus", "Train", "Uber"])
        else:
            descripition = "Sussy stuff"

        account_type = choice(account_types)
        new_expense = Expense(user_id=user_id, expense_amount=expense_amount, description=description,
                              expense_date=expense_date, expense_category=expense_category, account_type=account_type)
        db.session.add(new_expense)
    db.session.commit()


def add_budget_data():
    """
    This function generates random budget data for multiple users with varying numbers of budgets and
    categories.
    """
    # make a couple of budgets for each user, testing diff ways of randomising
    user_ids = generate_user_list()
    category_list = ["Donation", "Eating out", "Education", "Entertainment", "Groceries",
                     "Health", "Housing and Utilities", "Insurance", "Services", "Shopping",
                     "Travel and Transportation", "Miscellaneous & Other Expenses"]
    duration = "30 days"

    for user in user_ids:
        user_id = user
        date_start = str(date.today())
        amounts_list = []

        # random number of categories and corresponding amounts
        n = randint(4, 6)
        categories_list = sample(category_list, n)
        for j in range(n):
            amounts_list.append(str(round(uniform(0.01, 999.99), 2)))

        amounts = ", ".join(amounts_list)
        categories = ", ".join(sorted(categories_list))
        new_budget_data = Budget(user_id=user_id, categories=categories,
                                 amounts=amounts, date_start=date_start, duration=duration)
        db.session.add(new_budget_data)
        db.session.commit()


def add_investment_data():
    """
    This function adds 100 investment data entries to the database with randomly generated user IDs and
    investment types.
    """
    user_ids = generate_user_list()
    investment_types = ["Stock", "Cryptocurrency", "Custom Investment"]
    for i in range(100):
        user_id = choice(user_ids)
        investment_type = choice(investment_types)
        new_investment_data = Investment(
            user_id=user_id, investment_type=investment_type)
        db.session.add(new_investment_data)
    db.session.commit()


def add_bill_data():
    """
    This function generates random bill data for users with different bill names, due dates, and
    frequencies.
    """
    user_ids = generate_user_list()
    bills = ["Sydney Water", "Strata",
             "EnergyAustralia", "AGL Electricity", "AGL Gas"]
    bill_options = ["Monthly", "Quarterly",
                    "Biannual", "Annual", "Custom Days"]
    # each user has 3-5 bills to pay
    for user in user_ids:
        num_of_bills = randint(3, 5)
        user_id = user

        for i in range(num_of_bills):
            bill_name = bills[i]
            bill_option = choice(bill_options)
            bill_due_date = str(date.today() + timedelta(days=randint(1, 60)))
            # preset frequencies
            if bill_option != "Custom Days":
                bill_custom_freq = -1
                bill_description = bill_option + " " + bill_name
            # custom frequency
            else:
                bill_custom_freq = randint(1, 365)
                bill_description = bill_name + " every " + \
                    str(bill_custom_freq) + " days"

            new_bill_data = Bill(user_id=user_id, bill_name=bill_name, bill_description=bill_description,
                                 bill_due_date=bill_due_date, bill_options=bill_option, bill_custom_freq=bill_custom_freq)
            db.session.add(new_bill_data)
        db.session.commit()


def add_goal_data():
    """
    This function generates random goals data for users
    """
    user_ids = generate_user_list()
    goals = ["Buying a Lamborghini", "Reading a book", "Hosting a Ted X Talk",
             "Creating Hollywood Hills Account", "Buying a basketball court"]

    for user in user_ids:
        num_of_goals = randint(3, 5)
        user_id = user

        for i in range(num_of_goals):
            goal_name = goals[i]
            goal_amount = round(uniform(0.01, 9999.99), 2)

            if goal_name == "Buying a Lamborghini":
                goal_description = choice(
                    ["Only 47 Lamborghinis in my Lamborghini account", ""])
            elif goal_name == "Reading a book":
                goal_description = choice(["Like Book", ""])
            elif goal_name == "Hosting a Ted X Talk":
                goal_description = choice(
                    ["Where I talk about my Lamborghini account", ""])
            elif goal_name == "Creating Hollywood Hills Account":
                goal_description = choice(
                    ["Only 47 Hills in my Hollywood Hills account", ""])
            elif goal_name == "Buying a basketball court":
                goal_description = choice(
                    ["Tennis, Basketball, tennis, basketball", ""])

            goal_date = date.today() + timedelta(days=randint(1, 365 * 3))
            # total_contribution = uniform(0.00, goal_amount)
            contribution_frequency = choice(
                ["Weekly", "Fortnightly", "Monthly"])

            if contribution_frequency == "Weekly":
                next_date = date.today() + relativedelta(days=7)
                delta = goal_date - date.today()
                payments = delta.days / 7
                next_payment = round(goal_amount / payments, 2)

            elif contribution_frequency == "Fortnightly":
                next_date = date.today() + relativedelta(days=14)
                delta = goal_date - date.today()
                payments = delta.days / 14
                next_payment = round(goal_amount / payments, 2)

            elif contribution_frequency == "Monthly":
                next_date = date.today() + relativedelta(months=1)
                delta = goal_date - date.today()
                payment_per_day = goal_amount / delta.days
                next_payment = round((next_date - date.today()
                                      ).days * payment_per_day, 2)

            new_goal_data = Goal(user_id=user_id, goal_name=goal_name,
                                 goal_amount=goal_amount, goal_description=goal_description,
                                 goal_date=str(goal_date), contribution_frequency=contribution_frequency,
                                 next_contribution_date=next_date, next_contribution_amount=next_payment, cyclical_contribution=next_payment)

            db.session.add(new_goal_data)
        db.session.commit()


def add_stock_and_crypto_data():
    """
    This function generates stock and crypto data for each user
    """
    user_ids = generate_user_list()
    stock_names = ["Tesla", "Apple", "Microsoft",
                   "Amazon", "NVIDIA", "VISA", "Meta Platforms"]
    crypto_names = ["Bitcoin", "Ethereum", "Litecoin",
                    "Ripple", "Cardano", "Dogecoin", "Solana"]
    investment_types = ["Stock", "Crypto"]

    for user in user_ids:
        num_of_stock_and_crypto = randint(4, 6)
        user_id = user
        ticker_name = ""
        ticker_symbol = ""
        for i in range(num_of_stock_and_crypto):
            investment_type = choice(investment_types)
            if investment_type == "Stock":
                ticker_name = choice(stock_names)
                if ticker_name == "Tesla":
                    ticker_symbol = "TSLA"
                elif ticker_name == "Apple":
                    ticker_symbol = "APPL"
                elif ticker_name == "Microsoft":
                    ticker_symbol = "MSFT"
                elif ticker_name == "Amazon":
                    ticker_symbol = "AMZN"
                elif ticker_name == "NVIDIA":
                    ticker_symbol = "NVDA"
                elif ticker_name == "Visa":
                    ticker_symbol = "V"
                elif ticker_name == "Meta Platforms":
                    ticker_symbol = "META"

            else:
                ticker_name = choice(crypto_names)
                if ticker_name == "Bitcoin":
                    ticker_symbol = "bitcoin"
                elif ticker_name == "Ethereum":
                    ticker_symbol = "ethereum"
                elif ticker_name == "Litecoin":
                    ticker_symbol = "litecoin"
                elif ticker_name == "Ripple":
                    ticker_symbol = "ripple"
                elif ticker_name == "Cardano":
                    ticker_symbol = "cardano"
                elif ticker_name == "Dogecoin":
                    ticker_symbol = "dogecoin"
                elif ticker_name == "Solana":
                    ticker_symbol = "solana"

            total_price = round(uniform(0.01, 250.00), 2)
            # unit_price = randint(1, 5)
            order_date = date.today() - timedelta(days=randint(1, 60))
            new_stock_and_crypto_data = Stock_and_Crypto(user_id=user_id, ticker_name=ticker_name, ticker_symbol=ticker_symbol,
                                                         total_price=total_price, order_date=order_date, investment_type=investment_type)
            db.session.add(new_stock_and_crypto_data)
        db.session.commit()


def add_custom_investment_data():
    """
    This function generates some test data for custom investments for each user
    """
    user_ids = generate_user_list()
    descriptions = ["Collecting pokemon cards", "Collecting coins", "Hoarding rubbish bags",
                    "Buying antiques", "Investing in property"]
    # each user has 1-5 bills to pay
    for user in user_ids:
        num_of_custom_investments = randint(3, 5)
        user_id = user
        for i in range(num_of_custom_investments):
            description = descriptions[i]
            purchased_amount = round(uniform(0.01, 250.00), 2)
            sold_amount = round(uniform(0.01, 250.00), 2)
            sold_date = choice(
                [None, date.today() - timedelta(days=randint(1, 60))])
            if sold_date is not None:
                purchased_date = str(
                    sold_date - timedelta(days=randint(1, 60)))
            else:
                purchased_date = str(
                    date.today() - timedelta(days=randint(1, 60)))

            new_custom_investment_data = Custom_Investment(user_id=user_id, description=description, purchased_amount=purchased_amount,
                                                           sold_amount=sold_amount, purchased_date=purchased_date, sold_date=str(sold_date))
            db.session.add(new_custom_investment_data)
        db.session.commit()
