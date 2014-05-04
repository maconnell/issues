
# NOTE this is only called "issue.py" and not "issues.py" to avoid it shadowing the issues module namespace

from flask import Flask,g,flash,render_template,redirect,request,url_for
import db

from flask_wtf import Form
from wtforms import TextField,HiddenField,SelectField,PasswordField,IntegerField,TextAreaField,BooleanField
from wtforms.validators import DataRequired,InputRequired
from flask_login import login_required,login_user,logout_user,UserMixin,login_url,current_user
from flask_mail import Message

from issues import app,login_manager,mail

from issues.utils import admin_required,severity_array, text_for_severity, class_for_severity
from issues.db import get_db



@app.route('/issues', methods=('GET',))
@login_required
def issues():
    # list all issues
    db_issues=db.get_issues(get_db())

    # in order to remap severity levels to text we convert to standard dictionary here.
    issues=[]
    for db_issue in db_issues:
        issue=dict(db_issue)
        issue['severity_class']=class_for_severity( issue['severity'] )
        issue['severity']=text_for_severity( issue['severity'] )
        issues.append(issue)

    return render_template('issues.html',issues=issues)



@app.route('/issues/<id>', methods=('GET', 'POST'))
@login_required
def issue(id):

    # if id is >=0 we are editing an existing issue - GET returns a form filled with the current details, POST saves it
    # if id is <0  we are creating a new issue - GET returns a form filled with default values, POST saves it
    try:
        id=int(id)
    except ValueError:
        flash("Sorry - '%s' doesn't look like an integer"%id,"error")
        return redirect( url_for("index") )


    #Create a userlist from the current database
    user_choices=[] # Create a list of usernames for the new issue form
    user_list=db.get_users(get_db())
    for user in user_list: user_choices.append( (user['name'],user['name']) )

    # Create a specialised Form with the correct user choices
    class EditIssueForm(Form):
        owner= SelectField('Assign to', validators=[DataRequired()],choices=user_choices)
        short_text= TextField('Summary', validators=[DataRequired()])
        #long_text= TextField('Summary', validators=[DataRequired()])
        long_text= TextAreaField('Details')#, validators=[DataRequired()])
        estimated_time= IntegerField('Estimated time',validators=[InputRequired()],default=0) # NOTE InputRequired necessary to accept 0
        severity= SelectField('Severity',choices=severity_array,default=2,coerce=int) # NOTE: coerce to get int(2) not unicode(2)
        open=BooleanField('Open',default=True)
        issue_id=id

    form=EditIssueForm()

    if request.method=='GET':

        issue=db.get_issue(get_db(),id)
        if issue: # if we are editing an existing issue, fill in values, else new issue and defaults
            form.owner.data=issue['owner']
            form.short_text.data=issue['short_text']
            form.long_text.data=issue['long_text']
            form.severity.data=issue['severity']
            form.open.data=issue['open']

        return render_template('issue.html',form=form)

    if request.method=='POST': # posting a new issue form

        if form.validate():

            if id<0:
                ok=db.add_issue(get_db(),
                    reporter=g.user.get_id(),
                    owner=form.owner.data,
                    short_text=form.short_text.data,
                    long_text=form.long_text.data,
                    estimated_time=form.estimated_time.data,
                    severity=form.severity.data,
                    open=form.open.data)
                if ok:
                    flash('Created issue!')
                else:
                    flash('Failed to create issue (DB problem) :-(','error')
                return redirect( url_for("index") )

            else:
                ok=db.set_issue(get_db(),
                               id,
                               owner=form.owner.data,
                               short_text=form.short_text.data,
                               long_text=form.long_text.data,
                               estimated_time=form.estimated_time.data,
                               severity=form.severity.data,
                               open=form.open.data)
                if ok:
                    flash('Updated issue!')

                    #message=Message(subject='New issue created!',
                    #                recipients=['michael.connell@gmail.com'],
                    #                body="""
                    #                Here is some stuff about it...
                    #                """)
                    #mail.send(message)
                else:
                    flash('Failed to update issue (DB problem) :-(','error')
                return redirect( url_for("index") )

        else: # form didn't validate
            print form.severity,form.severity.data,type(form.severity.data)
            for field,errors in form.errors.items():
                for error in errors: flash('Failed to validate %s:%s'%(field,error),'error')
            return redirect( url_for("index") )

