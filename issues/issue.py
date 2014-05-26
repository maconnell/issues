
"""
Handle both the /issues issues list page and /issues/<id> page for creation/editing

NOTE this is only called "issue.py" and not "issues.py" to avoid it shadowing the issues module namespace
"""
from issues.mail import send_issue_mail
import os

from flask import Flask,g,flash,render_template,redirect,request,url_for
import db

from flask_wtf import Form
from werkzeug.utils import secure_filename
from wtforms import TextField,HiddenField,SelectField,PasswordField,IntegerField,TextAreaField,BooleanField
from wtforms.validators import DataRequired,InputRequired
from flask_login import login_required,login_user,logout_user,UserMixin,login_url,current_user

from issues import app,login_manager,mail

from issues.utils import admin_required,severity_array, text_for_severity, class_for_severity
from issues.db import get_db

from uploads import UploadForm

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
        formname=HiddenField('formname',default='EditIssue')
        owner= SelectField('Assign to', validators=[DataRequired()],choices=user_choices)
        short_text= TextField('Summary', validators=[DataRequired()])
        #long_text= TextField('Summary', validators=[DataRequired()])
        long_text= TextAreaField('Details')#, validators=[DataRequired()])
        estimated_time= IntegerField('Estimated time',validators=[InputRequired()],default=0) # NOTE InputRequired necessary to accept 0
        severity= SelectField('Severity',choices=severity_array,default=2,coerce=int) # NOTE: coerce to get int(2) not unicode(2)
        open=BooleanField('Open',default=True)
        issue_id=id

    edit_issue_form=EditIssueForm()
    new_att_form=UploadForm()
    new_att_form.issue_id=id

    print type(request.form)
    print dir(request.form)
    print request.form.items()
    print request.form.get('formname','UNKNOWN')


    # If GET, make all the forms and render the page
    if request.method=='GET':
        issue=db.get_issue(get_db(),id)
        if issue: # if we are editing an existing issue, fill in values, else new issue and defaults
            edit_issue_form.owner.data=issue['owner']
            edit_issue_form.short_text.data=issue['short_text']
            edit_issue_form.long_text.data=issue['long_text']
            edit_issue_form.severity.data=issue['severity']
            edit_issue_form.open.data=issue['open']

        # Get all attachments, make a list of tuples containing the filename (as given and uploaded under) and secure value that we actually saved
        atts=db.get_attachments(get_db(),id)
        attachment_list=[]
        for att in atts:
            attachment_list.append( (att['filename'] , secure_filename(att['filename'])) )

        return render_template('issue.html',form=edit_issue_form,attachments=attachment_list,new_att_form=new_att_form)

    # Else we should have a POST form submission, if not, bail:
    if request.method!='POST':
        flash('Unhandled method')
        return redirect(url_for("issues"))

    # method is POST, but which form is submitted?
    if request.form.get('formname')=='EditIssue': # posting a new issue form

        if edit_issue_form.validate():
            if id<0:
                id=db.add_issue(get_db(),
                    reporter=g.user.get_id(),
                    owner=edit_issue_form.owner.data,
                    short_text=edit_issue_form.short_text.data,
                    long_text=edit_issue_form.long_text.data,
                    estimated_time=edit_issue_form.estimated_time.data,
                    severity=edit_issue_form.severity.data,
                    open=edit_issue_form.open.data)
                if id == False:
                    flash('Failed to create issue (DB problem) :-(','error')
                    return redirect( url_for("issues") )
                else:
                    flash('Created issue!')
                    send_issue_mail(id,new=True)
                    return redirect( url_for("issue",id=id) )

            else:
                ok=db.set_issue(get_db(),
                               id,
                               owner=edit_issue_form.owner.data,
                               short_text=edit_issue_form.short_text.data,
                               long_text=edit_issue_form.long_text.data,
                               estimated_time=edit_issue_form.estimated_time.data,
                               severity=edit_issue_form.severity.data,
                               open=edit_issue_form.open.data)
                if ok:
                    flash('Updated issue!')
                    send_issue_mail(id,new=False)

                else:
                    flash('Failed to update issue (DB problem) :-(','error')
                return redirect( url_for("issue",id=id) )

        else: # form didn't validate
            print edit_issue_form.severity,edit_issue_form.severity.data,type(edit_issue_form.severity.data)
            for field,errors in edit_issue_form.errors.items():
                for error in errors: flash('Failed to validate %s:%s'%(field,error),'error')
            return redirect( url_for("index") )

    if request.form.get('formname')=='UploadAttachment':
        print 'Upload attachment'
        print new_att_form
        if new_att_form.validate_on_submit():
            file=request.files['filename']
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename)) # will throw on error
                db.add_attachment(get_db(),id,current_user.id,file.filename)
                return redirect(url_for('issue',id=id))
