
"""

Yeah, this is where all the mail gets sent


"""

from flask_mail import Message
from flask import flash,url_for
from issues import app,login_manager,mail
from db import get_db,get_issue,get_email






def send_issue_mail(id,new=True):
    try:
        issue=get_issue(get_db(),id)
        print issue
        if not issue:
            flash("Failed to mail about this issue since we failed to obtain issue by id %s"%str(id),'error')

        reporter_email=get_email(get_db(),issue['reporter'])
        owner_email=get_email(get_db(),issue['owner'])

        if reporter_email==owner_email:
            recipients=[reporter_email]
        else:
            recipients=[reporter_email,owner_email]

        if new:
            subject='New issue: %s'%issue['short_text']
        else:
            subject='Updated issue: %s'%issue['short_text']

        html="""

                    See <a href="%s">%s</a>

            """ % ( url_for("issue",id=id,_external=True), url_for("issue",id=id,_external=True) )

        message=Message(subject=subject,recipients=recipients,html=html)
        mail.send(message)
    except Exception as e:
        print 'send_issue_mail caught',e


