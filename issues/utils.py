
from flask import Flask,g,flash,render_template,redirect,request,url_for
import db

from flask_wtf import Form
from wtforms import TextField,HiddenField,SelectField,PasswordField,IntegerField,TextAreaField,BooleanField
from wtforms.validators import DataRequired,InputRequired
from flask_login import login_required,login_user,logout_user,UserMixin,login_url,current_user
from flask_mail import Message

from issues import app,login_manager,mail


def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    if not hasattr(g, 'db'):
        g.db = db.get_connection()
        #flash('got new connection %s'%str(g.db))
    return g.db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'db'): g.db.close()



# customised login_required based upon flask-login's but which takes account of admin field
# decorate routes with "@admin_required" instead of @login_required - then user must be both logged in and an admin
from flask import current_app
from functools import wraps
def admin_required(fn):
    @wraps(fn)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated(): return current_app.login_manager.unauthorized()
        # if current_user is authenticated then it should be a "proper" logged in user and thus have our admin field:
        admin = current_user.admin
        if not admin:
            print current_user.id,'not admin',current_user.admin,type(current_user.admin)
            flash("Sorry, you don't have admin permissions",'error')
            return redirect(url_for("index"),403)
            #return current_app.login_manager.unauthorized()
        return fn(*args, **kwargs)
    return decorated_view


