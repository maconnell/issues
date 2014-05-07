__author__ = 'mikec'

import uuid
from flask import Flask

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


upload_folder=os.path.abspath(os.path.join(os.path.dirname(__file__),'../uploads'))
print upload_folder

app.config['UPLOAD_FOLDER']=upload_folder
from flask_mail import Mail
mail=Mail(app)

import issues.auth
import issues.index
import issues.users
import issues.issue
import issues.db
import issues.auth
import issues.utils
import issues.settings
import issues.uploads

#default config file:
"""
# Flask:
DEBUG = True
MAX_CONTENT_LENGTH = 16 * 1024*1024 # for file uploads
UPLOAD_FOLDER='uploads'

# Mail:
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USE_SSL = False
MAIL_DEFAULT_SENDER='foo@gmail.com'
MAIL_USERNAME = 'foo@gmail.com'
MAIL_PASSWORD = 'password'


"""

