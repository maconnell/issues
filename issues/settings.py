
from flask import Flask,g,flash,render_template,redirect,request,url_for
import db

from flask_wtf import Form
from wtforms import TextField,HiddenField,SelectField,PasswordField,IntegerField,TextAreaField,BooleanField
from wtforms.validators import DataRequired,InputRequired
from flask_login import login_required,login_user,logout_user,UserMixin,login_url,current_user
from flask_mail import Message

from issues import app,login_manager,mail

from issues.utils import check_password,encrypt
from issues.db import get_db,set_user_password


class UpdatePasswordForm(Form):
    old_password= PasswordField('Current password', validators=[DataRequired()])
    new_password_1= PasswordField('New password', validators=[DataRequired()])
    new_password_2= PasswordField('New password again', validators=[DataRequired()])





@app.route('/settings', methods=('GET', 'POST'))
@login_required
def settings():

    update_password_form=UpdatePasswordForm()
    if update_password_form.validate_on_submit():

        info=db.get_user_info(get_db(),g.user.id)
        old_password_ok=check_password( info['password'] , update_password_form.old_password.data )
        new_passwords_match = update_password_form.new_password_1.data == update_password_form.new_password_2.data
        if old_password_ok and new_passwords_match:
            new_password_hash=encrypt(update_password_form.new_password_1.data)
            set_user_password(get_db(),g.user.id,new_password_hash)
            flash('Password updated')
        else:
            flash('Old password invalid or new passwords differ','error')

        return redirect( url_for('settings'))
    #elif other forms validate do those....

    else:
        # no forms validate
        return render_template('settings.html',update_password_form=update_password_form)

