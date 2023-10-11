from flask import Flask, request, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config
from flask_bootstrap import Bootstrap5
from flask_moment import Moment


app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'auth.login'
login.login_message = "Please log in to access this page."
bootstrap = Bootstrap5(app)
moment = Moment(app)

from app.routes import auth_routes, dropdown_routes, main_routes
