from flask import Flask, render_template, redirect, url_for, request, session, flash
import ibm_db
import sendgrid
import os
from dotenv import load_dotenv
from sendgrid.helpers.mail import Mail, Email, To, Content

app = Flask(__name__)
# secret key required to maintain unique user sessions
app.secret_key = 'f39c244d6c896864abe3310b839091799fed56007a438d637baf526007609fe0'

# establish connection with IBM Db2 Database
connection = ibm_db.connect("DATABASE=bludb;HOSTNAME=8e359033-a1c9-4643-82ef-8ac06f5107eb.bs2io90l08kqb1od8lcg.databases.appdomain.cloud;PORT=30120;SECURITY=SSL;UID=gyq42313;PWD=TRn8xYTPTGloNwQC;", "", "")

load_dotenv()  # load keys from .env
sg = sendgrid.SendGridAPIClient(api_key=os.environ.get(
    'SENDGRID_API_KEY'))  # set SendGrid API Key
# the address that sends emails to the users
from_email = Email("dhanushcodepro@gmail.com")

# Handle expense model according to ibm db




@app.route('/')
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        # ask user to sign in if not done already
        return redirect(url_for('signin'))
    # Fetch the list of expenses from db
    sql = 'select * from expenses where cid = '+str(session['id'])
    stmt = ibm_db.exec_immediate(connection, sql)   
    
    expense_list = {}
    i=0
    while (res:=ibm_db.fetch_assoc(stmt)) != False:
        expense_list[i] = res
        i+=1
    # go to homepage if signed in
    sql='select sum(eamount) from expenses where cid= '+str(session['id'])
    stmt = ibm_db.exec_immediate(connection, sql)
    sum_dict= ibm_db.fetch_assoc(stmt)
    sum = sum_dict['1']

    sql='select budget from users where id= '+str(session['id'])
    stmt = ibm_db.exec_immediate(connection, sql)
    budget_list= ibm_db.fetch_assoc(stmt)
    # budget = budget_list.values()
    for key,value in budget_list.items():
        pass
    rem = value - sum

    per = (sum/value)*100
    return render_template('dashboard.html', ex_list=expense_list,esum=sum,budget=value,rem=rem,per=per,name=session['username'])




@app.route('/addexpense')
def add():
    return render_template('addexpense.html')

@app.route('/addbudget')
def addb():
    sql='select budget from users where id= '+str(session['id'])
    stmt = ibm_db.exec_immediate(connection, sql)
    budget_list= ibm_db.fetch_assoc(stmt)
    # budget = budget_list.values()
    for key,value in budget_list.items():
        pass
    return render_template('addbudget.html',budget=value,id=session['id'])


@app.route('/addbudget/<int:id>',methods=['POST'])
def addbudget(id):
    budget = request.form['budget']
    sql = 'update users set budget = ? where id = '+str(id)
    # Add to the database here
    pstmt = ibm_db.prepare(connection, sql)
    ibm_db.bind_param(pstmt, 1, budget)
    ibm_db.execute(pstmt)
    return redirect('/dashboard')

@app.route('/addexpense', methods=['POST'])
def addexpense():
    date = request.form['date']
    expensename = request.form['expensename']
    amount = request.form['amount']
    category = request.form['category']
    sql = 'INSERT INTO expenses(edate,ename,eamount,ecategory,cid) VALUES(?,?,?,?,?)'
    # Add to the database here
    pstmt = ibm_db.prepare(connection, sql)
    ibm_db.bind_param(pstmt, 1, date)
    ibm_db.bind_param(pstmt, 2, expensename)
    ibm_db.bind_param(pstmt, 3, amount)
    ibm_db.bind_param(pstmt, 4, category)
    ibm_db.bind_param(pstmt, 5, session['id'])
    ibm_db.execute(pstmt)
    flash('Expense added Successfully')

    return redirect('/dashboard')


@app.route('/expense/update/<int:id>')
def update(id):
    # Get from the database
    sql = 'select * from expenses where id = '+str(id)
    # Add to the database here
    pstmt = ibm_db.prepare(connection, sql)
    ibm_db.execute(pstmt)
    acc = ibm_db.fetch_assoc(pstmt)
    return render_template('updateexpense.html',acc=acc)


@app.route('/edit', methods=['POST'])
def edit():
    id = request.form["id"]
    date = request.form['date']
    expensename = request.form['expensename']
    amount = request.form['amount']
    category = request.form['category']

    sql = 'update expenses set edate = ?,ename = ? ,eamount = ? ,ecategory = ? where id = '+str(id)
    # Add to the database here
    pstmt = ibm_db.prepare(connection, sql)
    ibm_db.bind_param(pstmt, 1, date)
    ibm_db.bind_param(pstmt, 2, expensename)
    ibm_db.bind_param(pstmt, 3, amount)
    ibm_db.bind_param(pstmt, 4, category)
    ibm_db.execute(pstmt)

    
    return redirect('/dashboard')


@app.route('/expense/delete/<int:id>', methods=['GET'])
def delete(id):
    # Database operation
    # flash(str(id))
    sql = 'delete from expenses where id = '+str(id)   #check if user is already registered
    pstmt = ibm_db.prepare(connection, sql)
    ibm_db.execute(pstmt)

    return redirect('/dashboard')


@app.route('/graph')
def graph():
    
    sql = 'select * from expenses where cid = '+str(session['id'])
    stmt = ibm_db.exec_immediate(connection, sql)
    expense_list = {}
    i=0
    while (res:=ibm_db.fetch_assoc(stmt)) != False:
        expense_list[i] = res
        i+=1
    total = 0
    household = 0
    food = 0
    entertainment = 0
    business = 0
    other = 0
    for key,value in expense_list.items():
        total += value['EAMOUNT']
        if value['ECATEGORY'] == 'household':
            household += value['EAMOUNT']
        elif value['ECATEGORY'] == 'food':
            food += value['EAMOUNT']
        elif value['ECATEGORY'] == 'entertainment':
            entertainment += value['EAMOUNT']
        elif value['ECATEGORY'] == 'business':
            business += value['EAMOUNT']
        elif value['ECATEGORY'] == 'other':
            other += value['EAMOUNT']

    return render_template('graph.html',  total=total, household=household, food=food, entertainment=entertainment, business=business, other=other)


@app.route('/signout')
def signout():
    session.pop('username', None)  # remove user session upon signing out
    return redirect('/')


@app.route('/signup')
def register():
    if 'username' in session:   #inform user if they're already signed in the same session
        flash('You are already signed in! Sign out to login with a different account')
        return redirect(url_for('dashboard'))

    else:    
        return render_template('signup.html') #take user to the registration page


@app.route('/signup', methods=['POST'])
def regform():
    uname = request.form['uname']   #get user id and password from the form
    email = request.form['email']   
    pwd = request.form['pass']
    print(uname,email,pwd)
    sql = 'SELECT * from users WHERE email=?'   #check if user is already registered
    pstmt = ibm_db.prepare(connection, sql)
    ibm_db.bind_param(pstmt, 1, email)
    ibm_db.execute(pstmt)

    acc = ibm_db.fetch_assoc(pstmt)

    if acc:     #inform user to sign in if they have an existing account
        flash('You are already a member. Please sign in using your registered credentials')

    else:
        sql = 'INSERT INTO users(username,password,email) VALUES(?,?,?)' #insert credentials of new user to the database
        pstmt = ibm_db.prepare(connection, sql)
        ibm_db.bind_param(pstmt, 1, uname)
        ibm_db.bind_param(pstmt, 2, pwd)
        ibm_db.bind_param(pstmt, 3, email)
        ibm_db.execute(pstmt)

        # to_email = To(uid)   #set user as recipient for confirmation email
        # subject = "Welcome to GetPlasma"
        # content = Content("text/html", "<p>Hello " + uname + ",</p><p>Thank you for registering to the GetPlasma Application!</p><p>If this wasn't you, then immediately report to our <a href=\"mailto:getplasmaproject@gmail.com\">admin</a> or just reply to this email.</p>")

        # email = Mail(from_email, to_email, subject, content) #construct email format
        # email_json = email.get()    #get JSON-ready representation of the mail object

        # response = sg.client.mail.send.post(request_body = email_json)  #send email by invoking an HTTP/POST request to /mail/send


        flash('Registration Successful! Sign in using the registered credentials to continue')


    return redirect(url_for('signin'))  #ask users to sign in after registration



@app.route('/signin')
def signin():
    if 'username' in session:  # inform user if they're already signed in the same session
        flash('You are already signed in! Sign out to login with a different account')
        return redirect(url_for('dashboard'))
    return render_template('login.html')  # take user to the sign in page


@app.route('/signinform', methods=['POST'])
def signinform():
    uid = request.form['email']  # get user id and password from the form
    pwd = request.form['pass']

    # check user credentials in the database
    sql = 'SELECT * from users WHERE email=? AND password=?'
    pstmt = ibm_db.prepare(connection, sql)
    ibm_db.bind_param(pstmt, 1, uid)
    ibm_db.bind_param(pstmt, 2, pwd)
    ibm_db.execute(pstmt)

    acc = ibm_db.fetch_assoc(pstmt)

    if acc: #if the user is already registered to the application
        session['username'] = acc['USERNAME']
        session['id'] = acc['ID']
        flash(session['username'] + str(session['id'])+'Signed in successfully!')
        return redirect(url_for('dashboard'))
        
    else:   #warn upon entering incorrect credentials
        flash('Incorrect credentials. Please try again!')
        return render_template('login.html')
if __name__ == '__main__':
    app.run(debug=True)