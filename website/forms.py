# Database code goes in here

import calendar

from flask_wtf import FlaskForm
from wtforms import (BooleanField, FloatField, PasswordField, SelectField,
                     StringField, RadioField, IntegerField, DecimalField, SubmitField)
from wtforms.fields import DateField
from wtforms.validators import Email, InputRequired, Length


# The `LoginForm` class is a Flask form that includes fields for email, password, and a checkbox for
# remembering the user.
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
                        InputRequired(), Email(message="Invalid email address")])
    password = PasswordField('Password', validators=[
                             InputRequired()])
    remember = BooleanField('Remember me for next time')

# Form class to sign up


class SignupForm(FlaskForm):
    email = StringField('Email', validators=[
                        InputRequired(), Email(message="Invalid email address")])
    password = PasswordField('Password', validators=[
                             InputRequired(), Length(min=8, max=30)])
    password2 = PasswordField('Re-enter your password', validators=[
        InputRequired(), Length(min=8, max=30)])
    first_name = StringField('First Name', validators=[
                             InputRequired(), Length(min=1, max=50)])
    last_name = StringField('Last Name', validators=[
                            InputRequired(), Length(min=1, max=50)])
    birthday = DateField("Birthday", validators=[InputRequired()])
    captcha = StringField("Please enter the text in the image:", validators=[
        InputRequired()])

# Form class to input expenses


class ExpenseForm(FlaskForm):
    amount = FloatField('Amount')
    category = SelectField('Category', choices=[
                           "Eating Out", "Entertainment", "Groceries", "Travel and Transport",
                           "Health", "Shopping", "Housing and Utilities", "Services", "Education", "Insurance", "Donations", "Miscellaneous"])
    description = StringField('Description')
    date = DateField("Date", validators=[InputRequired()])


class InvestmentForm(FlaskForm):
    share_amount = FloatField('Share Amount')
    stock_index = StringField('Stock Index')
    stock_name = StringField('Stock Name')


class ChangePasswordForm(FlaskForm):
    old_pswd = PasswordField('Old Password', validators=[
                             InputRequired(), Length(min=8, max=80)])
    new_pswd = PasswordField('New Password', validators=[
                             InputRequired(), Length(min=8, max=80)])
    new_pswd_2 = PasswordField('Retype New Password', validators=[
        InputRequired(), Length(min=8, max=80)])


class DeletionForm(FlaskForm):
    pswd = PasswordField('To confirm that you would like to delete your account, please enter your password:', validators=[
        InputRequired(), Length(min=8, max=80)])


# front end side of content EDIT THIS
class BillsForm(FlaskForm):
    bill_name = StringField('Bill Name (e.g. Sydney Water)', validators=[
        InputRequired()])
    # bill_amount = DecimalField("Bill Amount", validators=[InputRequired()])
    bill_desc = StringField(
        "(Optional) Bill Description (e.g. 'Quarterly Water Bill')")
    bill_due_date = DateField(
        "Upcoming Due Date", validators=[InputRequired()])
    bill_options = SelectField(label='Frequency', choices=['Monthly', 'Quarterly',
                                                           "Biannual", "Annual", "Custom Days"],  default='Quarterly')
    bill_custom_freq = IntegerField(label="Bill Cycle (Days)", default=1)


class GoalsForm(FlaskForm):
    goal_name = StringField('Goal', validators=[
        InputRequired()])
    goal_desc = StringField(
        "Goal Description")
    goal_amount = FloatField(
        "Goal Amount", validators=[InputRequired()])
    goal_date = DateField('Goal Date', validators=[
        InputRequired()])
    contribution_frequency = SelectField(label='Contribution Frequency', choices=['Weekly', 'Fortnightly',
                                                                                  "Monthly"],  default='Weekly')


class BudgetSharingForm(FlaskForm):
    email = StringField('Email', validators=[
                        InputRequired(), Email(message="Invalid email address")])


class IncomeForm(FlaskForm):
    amount = FloatField('Amount')
    description = StringField('Description')
    date = DateField("Date", validators=[InputRequired()])
