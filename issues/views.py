__author__ = 'mikec'
"""
This file contains the application server
"""

from flask import Flask,g,flash,render_template,redirect,request,url_for
import db

from flask_login import current_user

from issues import app,login_manager,mail

from issues.utils import admin_required,get_db


@app.route('/')
def index():
    issues=db.get_issues(get_db())
    return render_template('index.html',issues=issues,current_user=current_user)




if __name__=='__main__':
    app.run(debug=True)