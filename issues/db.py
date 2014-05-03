__author__ = 'mikec'
"""

Contains all the db related code,

"""
import sqlite3,datetime,random,string

def get_connection(filename='todo.db'):
    """
    opens the database and returns a connection object
    if filename is None, use a temporary in memory db
    """
    if not filename: filename=":memory:"

    # PARSE_DECLTYPES converts text into the correct python type for the column (ie sql DATETIME to Python datetime)
    # we must also use TIMESTAMP as column definition instead of DATETIME in order for Python to convert it for us
    con = sqlite3.connect(filename,detect_types=sqlite3.PARSE_DECLTYPES)

    # sqlite3 doesn't respect foreign keys by default, but v4 does - this must be done for every connection
    cur = con.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    con.commit()

    # results from sqlite will be accesaable both as a tuple or as a dict
    con.row_factory = sqlite3.Row

    return con


def createDB(filename='todo.db',script='db.sql'):

    # Create tables
    con=get_connection(filename)
    con.executescript( open(script).read() )
    con.commit()

    # Add internal robot user, don't need to remember their password
    password=''.join(random.choice( string.ascii_letters ) for i in range(16))
    create_user(con,'robot', '', password, active=False)
    con.commit()

    # create a default account for development
    create_user(con,'admin', '', password='admin', active=True)


    con.close()

import unittest,os
class TestDataBase(unittest.TestCase):

    def setUp(self):
        self.filename='test.db'
        if os.path.exists(self.filename): os.remove(self.filename)
        createDB(self.filename)
        con=get_connection(self.filename)
        # these 3 users used for non-user tests
        create_user(con,'user1','email','password')
        create_user(con,'user2','email','password')
        create_user(con,'user3','email','password')
        con.commit()

    def test_users(self):
        con=get_connection(self.filename)
        self.assertTrue(  create_user(con,'user','email','password') )
        self.assertFalse( create_user(con,'user','email','password') )
        self.assertFalse( create_user(con,'user2','email',password=None) )
        self.assertIsNotNone( get_userid(con,'user'))
        self.assertIsNone( get_userid(con,'userXXX'))

    def test_issues(self):
        con=get_connection(self.filename)
        self.assertTrue( add_todo(con,'user1','user2','short_text','long_text',estimated_time=1) )
        self.assertTrue( add_todo(con,'user1','user2','short_text','long_text') )
        self.assertFalse( add_todo(con,'userXXX','user2','short_text','long_text') )
        self.assertFalse( add_todo(con,'user1','userXXX','short_text','long_text') )

def test_db(filename='todo.db'):

    con = get_connection(filename)



    con.execute("INSERT INTO users (name,email) VALUES ('mikec','michael.connell@gmail.com')")
    con.execute("INSERT INTO users (name,email) VALUES ('fred','fred@nowhere')")
    #cur.execute("INSERT INTO user (name,email) VALUES ('fred','fred@nowhere')") # must fail since fred already exists

    con.execute("INSERT INTO issues (reporter,owner,short_text) VALUES ('mikec','mikec','issue 1')")
    con.execute("INSERT INTO issues (reporter,owner,short_text) VALUES ('mikec','mikec','issue 2')")
    #cur.execute("INSERT INTO issue (shorttext) VALUES ('issue must fail')") # must fail - require owner & reporter
    #cur.execute("INSERT INTO issue (reporter,owner,shorttext) VALUES ('not a user','not a user either','issue 3')") # must fail, reporter and owner must exist


    # mimic finding an issue to comment on:
    results=con.execute("SELECT id FROM issues WHERE short_text LIKE :issuename",{'issuename':'issue 1'}).fetchall()
    if len(results)>0: issueid=results[0][0]

    con.execute("INSERT INTO comments (owner,issue,text) VALUES ('mikec',:issueid,'comment on issue 1')",{'issueid':issueid})
    #cur.execute("INSERT INTO comment (owner,issue,text) VALUES (NULL,'issue 1','comment on issue 1')") # must fail - owner must not be NULL
    #cur.execute("INSERT INTO comment (owner,issue,text) VALUES ('not a user','issue 123','comment on issue 1')") # must fail - owner must exist in user table
    con.commit()


    rows=con.execute("SELECT * FROM comment")
    for row in rows: print(row)



    con.close()

    #cur.execute("select * from people where name_last=:who and age=:age", {"who": who, "age": age})


def create_user(con,username,email,password,active=True):
    """

    """
    print 'create_user',username
    try:
        con.execute("INSERT INTO users (name,email,password,active) VALUES (?,?,?,?)",(username,email,password,active))
        con.commit()
        return True
    except sqlite3.Error,e:
        pass #print 'Got error creating user',username,e
    return False


def get_user_info(con,username):
    """
    return users details or None if not found
    """
    print username,type(username)
    rows=con.execute('SELECT * FROM users WHERE name = ?',(username,))
    rows=rows.fetchall()
    if len(rows)<1: return None # username not found
    return rows[0]

def authenticate_user(con,username,password):
    """
    if password is correct for given user and they are active, return True else False
    """
    info=get_user_info(con,username)
    if not info: return False
    stored_password=info['password']
    active=info['active']
    if password==stored_password and active: return True
    return False


def get_userid(con,name):
    try:
        rows=con.execute("SELECT id FROM users WHERE name = ?",(name,))
        rows=rows.fetchall()
        if len(rows)!=1: return None
        return rows[0]['id']
    except sqlite3.Error,e:
        print e
    return None


def add_todo(con,reporter,owner,short_text,long_text,estimated_time=0,created_date=None,last_edit_date=None):
    """
    created_date and last_edit_date should be datatime objects if not None
    """
    if not created_date: created_date=datetime.datetime.now()
    if not last_edit_date: last_edit_date=datetime.datetime.now()

    # BUG There should be a clever way to perform the INSERT in SQL without first extracting the user ids here
    reporterid=get_userid(con,reporter)
    ownerid=get_userid(con,owner)

    try:
        con.execute("INSERT INTO issues (reporter,owner,short_text,long_text,estimated_time,created_date,last_edit_date) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (reporterid,ownerid,short_text,long_text,estimated_time,created_date,last_edit_date))

        con.commit()
        return True
    except sqlite3.Error,e:
        pass #print 'Got error add_todo',e
    return False

def set_todo(con, id, owner, short_text, long_text, estimated_time):
    last_edit_date=datetime.datetime.now()

    # BUG There should be a clever way to perform the INSERT in SQL without first extracting the user ids here
    ownerid=get_userid(con,owner)

    try:
        con.execute('''UPDATE issues
                    SET owner=?,
                    short_text=?,
                    long_text=?,
                    estimated_time=?,
                    last_edit_date=?
                    WHERE id = ?;''',
                    (ownerid,short_text,long_text,estimated_time,last_edit_date,id))
        con.commit()
        return True
    except sqlite3.Error,e:
        print 'Got error set_todo',e
    return False


def get_issues(con):
    """
    get all the issues
    BUG: should remove long_text from the query, only return it in get_issue(con,id)
    """
    query="""
    SELECT issue.id,
           owner.name as owner,
           reporter.name as reporter,
           issue.short_text,
           issue.long_text,
           issue.estimated_time,
           issue.created_date,
           issue.last_edit_date,
           issue.closed_date
    FROM issues issue
    JOIN   users owner on owner.id = issue.owner
    JOIN users reporter on reporter.id=issue.reporter;
    """
    rows=con.execute(query)
    return rows.fetchall()

def get_issue(con,id):
    """
    """
    query="""
    SELECT issue.id,
           owner.name as owner,
           reporter.name as reporter,
           issue.short_text,
           issue.long_text,
           issue.estimated_time,
           issue.created_date,
           issue.last_edit_date,
           issue.closed_date
    FROM issues issue
    JOIN   users owner on owner.id = issue.owner
    JOIN users reporter on reporter.id=issue.reporter
    WHERE issue.id = ?;
    """
    rows=con.execute(query,(id,))
    return rows.fetchall()[0]



def get_users(con):
    # Get a list of all usernames, excluding our special robot, and inactive accounts
    rows=con.execute("SELECT * FROM users u WHERE u.name IS NOT 'robot' AND u.active IS 1")
    return rows.fetchall()



if __name__=='__main__':
    #createDB()
    unittest.main()


def set_user_admin(con,username,isadmin):
    print 'db.set_user_admin',username,isadmin
    try:
        con.execute("UPDATE users SET admin = ? WHERE name=?",(isadmin,username))
        con.commit()
        return True
    except sqlite3.Error,e:
        print 'Got error set_user_admin',e
    return False

