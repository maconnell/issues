"""
user admin page - create and delete users
We shouldn't expand this too much, instead let admins edit via the user settings page
Should be limited to:
    add user by name
    list users
        - toggle admin flag
        - toggle active flag

"""
from flask import Flask,g,flash,render_template,redirect,request,url_for
import db

from flask_wtf import Form
from wtforms import TextField,HiddenField,SelectField,PasswordField,IntegerField,TextAreaField,BooleanField
from wtforms.validators import DataRequired,InputRequired
from flask_login import login_required,login_user,logout_user,UserMixin,login_url,current_user
from flask_mail import Message

from issue import app,login_manager,mail

from issues.utils import admin_required
from issues.db import get_db
from utils import encrypt

class AddUserForm(Form):
    action = HiddenField('action',default='CREATE')
    name = TextField('username', validators=[DataRequired()])
    email= TextField('email address', validators=[DataRequired()])
    password = TextField('password', validators=[DataRequired()])

class DeleteUserForm(Form):
    action = HiddenField('action',default='DELETE')
    username = HiddenField('username', validators=[DataRequired()])

class UserAdminForm(Form):
    action = HiddenField('action',default='ADMIN')
    username = HiddenField('username', validators=[DataRequired()])
    admin=BooleanField('admin')

@app.route('/users', methods=('GET', 'POST'))
@admin_required
def user():

    if request.method=='POST':
        action=request.form['action']
        if action=='DELETE':
            delete_user_form= DeleteUserForm()
            if delete_user_form.validate():
                username=request.form['username']
                if username=='admin' or username=='guest':
                    flash("admin and guest accounts can't be deleted",'error')
                else:
                    ok=db.delete_user(get_db(),username)
                    if ok: flash('Deleted %s'%username,'ok')
                    else:  flash('Failed to delete %s'%username,'error')
            else:
                flash('delete form failed to validate','error')

        elif action=='CREATE':
            add_user_form = AddUserForm() # create from current form values

            if add_user_form.validate():
                password=add_user_form.password.data
                password_hash=encrypt(password)
                ok=db.create_user(get_db(),add_user_form.name.data,add_user_form.email.data,password_hash)
                if ok:
                    flash('New user %s created'%add_user_form.name.data,'ok')
                else:
                    flash('Sorry, could not create user %s'%add_user_form.name.data,'error') # validation OK, but DB failed
            else: # posted a invalid form
                flash('Please fill in all fields','warning')

        elif action=="ADMIN":
            admin_form=UserAdminForm()
            db.set_user_admin(get_db(),admin_form.username.data,admin_form.admin.data)


        # By default reget the page, can't return a new render here as the existing form would pollute the creation values of the new forms
        return redirect('/users')

    else: # GET
        add_user_form = AddUserForm()
        userlist=db.get_users(get_db())

        # Since get_users doesnt return a list of result, we have to convert the structure in order to insert the delete
        # user form into the list
        userlist2=[]
        for user in userlist:
            name=user['name']
            isadmin=user['admin']
            newrow=list(user)+[DeleteUserForm(username=name),UserAdminForm(username=name,admin=isadmin)]
            userlist2.append(newrow)

        return render_template('user.html', add_user_form=add_user_form, userlist=userlist2)




