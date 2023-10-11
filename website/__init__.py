import os
import random
import string

from captcha.image import ImageCaptcha
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
DB_NAME = "budget_database.db"
characters = string.ascii_letters + string.digits
# CAPTCHA_TEXT = ''.join(random.choices(characters, k=5))
CAPTCHA_TEXT = "cassowary"


def create_app():
    # Initialise flask app and designate the Template and Static folders
    app = Flask(__name__, template_folder='Templates', static_folder='Static')

    # Import bootstrap
    bootstrap = Bootstrap(app)

    # Set the secret key for user session cookies (not important but flash messages need it to work)
    app.config["SECRET_KEY"] = "secret"
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_NAME}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Link the db to the app
    db.init_app(app)

    # Import the routes from various .py files
    from .auth import auth
    from .data import add_user_data, initialise_db_contents
    from .uploads import uploads
    from .views import views

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(uploads, url_prefix='/')

    from .models import User

    with app.app_context():
        # check if exists first?
        #db.drop_all()
        db.create_all()
        # after creating db, populate it, comment this after ###
        #initialise_db_contents()

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Clean up unused files on startup
    static_path = app.static_folder
    files = os.listdir(static_path)
    for file in files:
        if file.endswith(".csv") or file.endswith(".ics"):
            os.remove(os.path.join(static_path, file))

    # Make a new captcha each time the app is run

    create_captcha(CAPTCHA_TEXT)

    return app


def create_db(app):
    if not os.path.exists("website/" + DB_NAME):
        db.create_all(app=app)


def create_captcha(random_string):
    image = ImageCaptcha(width=280, height=90)
    text = random_string
    data = image.generate(text)
    image.write(text, "website/Static/images/CAPTCHA.png")
    return text
