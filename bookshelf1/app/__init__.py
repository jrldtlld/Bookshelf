from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap


app = Flask(__name__)
db = SQLAlchemy(app)
app.config.from_pyfile('config.py')
bootstrap = Bootstrap(app)

from models import Users, Books
from forms import RegistrationForm, LoginForm, Search
from app import view

db.create_all()
