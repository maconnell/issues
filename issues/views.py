__author__ = 'mikec'
"""
This file contains the application server
"""

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
        ok=db.authenticate_user(get_db(),username,form['password'].data)
        if ok:
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


@app.route('/')
def index():
    issues=db.get_issues(get_db())
    return render_template('index.html',issues=issues,current_user=current_user)



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
                ok=db.create_user(get_db(),add_user_form.name.data,add_user_form.email.data,add_user_form.password.data)
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



















if __name__=='__main__':
    app.run(debug=True)