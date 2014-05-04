
from flask import Flask,g,flash,render_template,redirect,request,url_for
import db

from flask_wtf import Form
from wtforms import TextField,HiddenField,SelectField,PasswordField,IntegerField,TextAreaField,BooleanField
from wtforms.validators import DataRequired,InputRequired
from flask_login import login_required,login_user,logout_user,UserMixin,login_url,current_user
from flask_mail import Message

from issues import app,login_manager,mail
from issues.db import get_db
from issues.utils import check_password


class LoginForm(Form):
    username= TextField('username', validators=[DataRequired()])
    password= PasswordField('password', validators=[DataRequired()])


from flask_login import UserMixin
def get_user_object(username):
    """
    return a User object suitable for flask-login with the given username
    """
    info=db.get_user_info(get_db(),username)
    if not info: return None # shouldn't every happen since they should be logged in
    user=UserMixin()
    user.id=username
    user.admin=info['admin']
    return user


# Flask-login requires this to return a User class or None.
@login_manager.user_loader
def load_user(username):
    return get_user_object(username)

# Store current user (if logged in) for current request
@app.before_request
def before_request():
    if current_user and current_user.get_id(): g.user = current_user

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username=form['username'].data
        password=form['password'].data
        info=db.get_user_info(get_db(),username)

        active=info['active']
        password_ok=check_password( info['password'] , password )

        print active,password_ok,info['password'] , password
        if active and password_ok:
            user=get_user_object(username)
            login_user(user,remember=True) # tells Flask-login to mark us as logged in
            flash("Logged in successfully.")
            return redirect(request.args.get("next") or url_for("index"))
        else:
            flash("Failed to authenticate",'error')
            return render_template("login.html", form=form),401

    return render_template("login.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('/')
