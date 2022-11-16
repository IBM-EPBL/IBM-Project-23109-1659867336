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
connection = ibm_db.connect(
    "DATABASE=bludb;HOSTNAME=815fa4db-dc03-4c70-869a-a9cc13f33084.bs2io90l08kqb1od8lcg.databases.appdomain.cloud;PORT=30367;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=fzx82079;PWD=Gemfhl3b2DRTeUqB;", "", "")

load_dotenv()  # load keys from .env
sg = sendgrid.SendGridAPIClient(api_key=os.environ.get(
    'SENDGRID_API_KEY'))  # set SendGrid API Key
# the address that sends emails to the users
from_email = Email("dhanushcodepro@gmail.com")

# Handle expense model according to ibm db


class Expense():
    #db = ibm_db.prepare()
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50), nullable=False)
    expensename = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=False)


@app.route('/')
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        # ask user to sign in if not done already
        return redirect(url_for('signin'))
    # Fetch the list of expenses from db
    expenses = list()
    # go to homepage if signed in
    return render_template('dashboard.html', pred=session['username'], data=expenses)


@app.route('/')
def add():
    return render_template('add_expense.html')


@app.route('/addexpense', methods=['POST'])
def addexpense():
    date = request.form['date']
    expensename = request.form['expensename']
    amount = request.form['amount']
    category = request.form['category']

    # Add to the database here
    expense = Expense(date=date, expensename=expensename,
                      amount=amount, category=category)
    db.session.add(expense)
    db.session.commit()

    return redirect('/expenses')


@app.route('/update/<int:id>')
def update(id):
    # Get from the database
    expense = Expense.query.filter_by(id=id).first()
    return render_template('update_expense.html', expense=expense)


@app.route('/edit', methods=['POST'])
def edit():
    id = request.form["id"]
    date = request.form['date']
    expensename = request.form['expensename']
    amount = request.form['amount']
    category = request.form['category']

    # Database part
    expense = Expense.query.filter_by(id=id).first()
    expense.date = date
    expense.expensename = expensename
    expense.amount = amount
    expense.category = category

    db.session.commit()
    return redirect('/expenses')


@app.route('/graph')
def graph():
    expenses = Expense.query.all()

    total = 0
    household = 0
    food = 0
    entertainment = 0
    business = 0
    other = 0
    for expense in expenses:
        total += expense.amount
        if expense.category == 'household':
            household += expense.amount
        elif expense.category == 'food':
            food += expense.amount
        elif expense.category == 'entertainment':
            entertainment += expense.amount
        elif expense.category == 'business':
            business += expense.amount
        elif expense.category == 'other':
            other += expense.amount

    return render_template('graph.html', expenses=expenses, total=total, household=household, food=food, entertainment=entertainment, business=business, other=other)


@app.route('/signout')
def signout():
    session.pop('username', None)  # remove user session upon signing out
    return redirect('/')


@app.route('/register')
def register():
    if 'username' in session:  # inform user if they're already signed in the same session
        flash('You are already signed in! Sign out to login with a different account')
        return redirect(url_for('dashboard'))

    else:
        # take user to the registration page
        return render_template('signup.html')


@app.route('/regform', methods=['POST'])
def regform():
    # get user details from the registration form
    i = [i for i in request.form.values()]
    uname = i[0]
    uid = i[1]
    pwd = i[2]

    sql = 'SELECT * from donor WHERE email=?'  # check if user is already registered
    pstmt = ibm_db.prepare(connection, sql)
    ibm_db.bind_param(pstmt, 1, uid)
    ibm_db.execute(pstmt)

    acc = ibm_db.fetch_assoc(pstmt)

    if acc:  # inform user to sign in if they have an existing account
        flash('You are already a member. Please sign in using your registered credentials')

    else:
        # insert credentials of new user to the database
        sql = 'INSERT INTO donor VALUES(?,?,?)'
        pstmt = ibm_db.prepare(connection, sql)
        ibm_db.bind_param(pstmt, 1, uid)
        ibm_db.bind_param(pstmt, 2, pwd)
        ibm_db.bind_param(pstmt, 3, uname)
        ibm_db.execute(pstmt)

        to_email = To(uid)  # set user as recipient for confirmation email
        subject = "Welcome to GetPlasma"
        content = Content("text/html", "<p>Hello " + uname +
                          ",</p><p>Thank you for registering to the GetPlasma Application!</p><p>If this wasn't you, then immediately report to our <a href=\"mailto:getplasmaproject@gmail.com\">admin</a> or just reply to this email.</p>")

        email = Mail(from_email, to_email, subject,
                     content)  # construct email format
        email_json = email.get()  # get JSON-ready representation of the mail object

        # send email by invoking an HTTP/POST request to /mail/send
        response = sg.client.mail.send.post(request_body=email_json)

        flash(
            'Registration Successful! Sign in using the registered credentials to continue')

    # ask users to sign in after registration
    return redirect(url_for('login'))


@app.route('/signin')
def signin():
    if 'username' in session:  # inform user if they're already signed in the same session
        flash('You are already signed in! Sign out to login with a different account')
        return redirect(url_for('dashboard'))
    return render_template('signin.html')  # take user to the sign in page


@app.route('/signinform', methods=['POST'])
def signinform():
    uid = request.form['uid']  # get user id and password from the form
    pwd = request.form['pwd']

    # check user credentials in the database
    sql = 'SELECT uname from donor WHERE email=? AND pwd=?'
    pstmt = ibm_db.prepare(connection, sql)
    ibm_db.bind_param(pstmt, 1, uid)
    ibm_db.bind_param(pstmt, 2, pwd)
    ibm_db.execute(pstmt)

    acc = ibm_db.fetch_assoc(pstmt)

    if acc:  # if the user is already registered to the application
        session['username'] = acc['UNAME']
        flash('Signed in successfully!')
        return redirect(url_for('dashboard'))

    else:  # warn upon entering incorrect credentials
        flash('Incorrect credentials. Please try again!')
        return render_template('signin.html')
