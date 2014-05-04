
# NOTE this is only called "issue.py" and not "issues.py" to avoid it shadowing the issues module namespace

from flask import Flask,g,flash,render_template,redirect,request,url_for
import db

from flask_wtf import Form
from wtforms import TextField,HiddenField,SelectField,PasswordField,IntegerField,TextAreaField,BooleanField
from wtforms.validators import DataRequired,InputRequired
from flask_login import login_required,login_user,logout_user,UserMixin,login_url,current_user
from flask_mail import Message

from issues import app,login_manager,mail

from issues.utils import admin_required
from issues.db import get_db




class IncompleteSetIssueForm(Form):
    # NOTE: We can't declare all fields here since they aren't known when this class is defined - user list for owner field
    # So we subclass in /issues handler, adding a owner SelectField with the correct choices

    short_text= TextField('Summary', validators=[DataRequired()])
    long_text= TextField('Summary', validators=[DataRequired()])
    long_text= TextAreaField('Details')#, validators=[DataRequired()])
    estimated_time= IntegerField('Estimated time',validators=[InputRequired()],default=0) # NOTE InputRequired necessary to accept 0


@app.route('/issues', methods=('GET', 'POST'))
@login_required
def issues():

    #Create a userlist from the current database
    user_choices=[] # Create a list of usernames for the new issue form
    user_list=db.get_users(get_db())
    for user in user_list: user_choices.append( (user['name'],user['name']) )
    # Create a specialised Form with the correct user choices
    class AddIssueForm(IncompleteSetIssueForm):
        owner= SelectField('Assign to', validators=[DataRequired()],choices=user_choices)

    if request.method=='GET':

        issues=db.get_issues(get_db())
        add_issue_form=AddIssueForm()

        return render_template('issues.html',issues=issues,add_issue_form=add_issue_form)

    if request.method=='POST': # posting a new issue form
        add_issue_form=AddIssueForm()

        if add_issue_form.validate():
            print 'adding issue to db...'
            ok=db.add_todo(get_db(),
                           reporter=g.user.get_id(),
                           owner=add_issue_form.owner.data,
                           short_text=add_issue_form.short_text.data,
                           long_text=add_issue_form.long_text.data,
                           estimated_time=add_issue_form.estimated_time.data)
            if ok:
                flash('Created new issue!')
                #message=Message(subject='New issue created!',
                #                recipients=['michael.connell@gmail.com'],
                #                body="""
                #                Here is some stuff about it...
                #                """)
                #mail.send(message)
            else:
                flash('Failed to create new issue (DB problem) :-(','error')
        else:
            for field,errors in add_issue_form.errors.items():
                for error in errors: flash('Failed to validate %s:%s'%(field,error),'error')
        return redirect('/issues')



@app.route('/issues/<int:id>', methods=('GET', 'POST'))
@login_required
def issue(id):

    #Create a userlist from the current database
    user_choices=[] # Create a list of usernames for the new issue form
    user_list=db.get_users(get_db())
    for user in user_list: user_choices.append( (user['name'],user['name']) )
    # Create a specialised Form with the correct user choices
    class EditIssueForm(IncompleteSetIssueForm):
        owner= SelectField('Assign to', validators=[DataRequired()],choices=user_choices)
        issue_id=id

    if request.method=='GET':

        issue=db.get_issue(get_db(),id)
        form=EditIssueForm()
        form.owner.data=issue['owner']
        form.short_text.data=issue['short_text']
        form.long_text.data=issue['long_text']

        if issue:
            return render_template('issue.html',issue=issue,form=form)
        else:
            flash("Failed to locate issue %d"%id,"error")
            return redirect('/issues')

    if request.method=='POST': # posting a new issue form
        form=EditIssueForm()

        if form.validate():
            print 'setting issue to db...'
            ok=db.set_todo(get_db(),
                           id,
                           owner=form.owner.data,
                           short_text=form.short_text.data,
                           long_text=form.long_text.data,
                           estimated_time=form.estimated_time.data)
            if ok:
                flash('Updated issue!')
                #message=Message(subject='New issue created!',
                #                recipients=['michael.connell@gmail.com'],
                #                body="""
                #                Here is some stuff about it...
                #                """)
                #mail.send(message)
                return redirect('/issues')
            else:
                flash('Failed to update issue (DB problem) :-(','error')
                return redirect('/issues/%d'%id)
        else:
            for field,errors in form.errors.items():
                for error in errors: flash('Failed to validate %s:%s'%(field,error),'error')
            return redirect('/issues/%d'%id)

