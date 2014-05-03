__author__ = 'mikec'

import uuid
from flask import Flask
from flask_mail import Mail

app = Flask(__name__)
app.secret_key=uuid.uuid4().hex

import flask_wtf
flask_wtf.CsrfProtect(app)

# Init flask-login:
from flask_login import LoginManager,login_url
login_manager = LoginManager()
login_manager.login_view=login_url('/login')
login_manager.init_app(app)

import os.path
app.config.from_pyfile( os.path.expanduser('~/.issues.cfg') )


mail=Mail(app)

import issues.views
import issues.db



#default config file:
"""
DEBUG = True
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USE_SSL = False
MAIL_DEFAULT_SENDER='foo@gmail.com'
MAIL_USERNAME = 'foo@gmail.com'
MAIL_PASSWORD = 'password'


"""

