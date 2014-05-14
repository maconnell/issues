from issues import app

"""
Installing, first run
1. setup virtual env (TODO)
2. run db.createDB, resulting issues.db should be located in head directory (besides this file)
3. copy default section from issues/__init__.py to ~/.issues.cfg and edit to taste
4. login is as admin/admin and change password!
"""

app.run(debug=True,host='0.0.0.0',port=8080)
