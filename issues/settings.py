
from flask import Flask,g,flash,render_template,redirect,request,url_for
import db

from flask_wtf import Form
from wtforms import TextField,HiddenField,SelectField,PasswordField,IntegerField,TextAreaField,BooleanField
from wtforms.validators import DataRequired,InputRequired
from flask_login import login_required,login_user,logout_user,UserMixin,login_url,current_user
from flask_mail import Message

from issues import app,login_manager,mail

from issues.utils import admin_required,get_db



@app.route('/settings', methods=('GET', 'POST'))
@login_required
def settings():
    flash('Sorry - user settings TBD','warning')
    return redirect( url_for('index'))
