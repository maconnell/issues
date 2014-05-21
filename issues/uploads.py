from flask import send_from_directory
from flask import Flask,g,flash,render_template,redirect,request,url_for
from flask.templating import render_template_string
from wtforms import FileField, HiddenField
from flask_wtf.form import Form

from issues import app,login_manager,mail
import os
from werkzeug.utils import secure_filename


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    print 'uploaded_file:',filename,app.config['UPLOAD_FOLDER']
    return send_from_directory(app.config['UPLOAD_FOLDER'],filename)

class UploadForm(Form):
    formname=HiddenField('formname',default='UploadAttachment')
    filename=FileField()

#
# @app.route('/uploads', methods=['GET', 'POST'])
# def upload_file():
#     form=UploadForm()
#     if form.validate_on_submit():
#         file=request.files['filename']
#         if file:
#             filename = secure_filename(file.filename)
#             file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#             return redirect(url_for('uploaded_file',filename=filename))
#     return render_template_string(
#         '''
#     <!doctype html>
#     <title>Upload new File</title>
#     <h1>Upload new File</h1>
#         <div class="panel-body">
#
#         <form method="POST" action="" method="post" enctype="multipart/form-data" class="form" role="form">
#             {{ form.hidden_tag() }}
#
#             <div class="form-inline">
#
# {{ form.filename() }}
#
#             <input type="submit" class="btn btn-success btn-sm" value="Update">
#
#             </div>
#         </form>
#
#     </div>
#
#     <form >
#       <p>
#
#     </form>
#     ''',form=form)
