from flask import Flask, render_template, redirect, url_for, request, session, flash
import ibm_db
import sendgrid
import os
from dotenv import load_dotenv
from sendgrid.helpers.mail import Mail, Email, To, Content

app = Flask(__name__)
#secret key required to maintain unique user sessions
app.secret_key = 'f39c244d6c896864abe3310b839091799fed56007a438d637baf526007609fe0'

#establish connection with IBM Db2 Database
connection = ibm_db.connect("DATABASE=bludb;HOSTNAME=8e359033-a1c9-4643-82ef-8ac06f5107eb.bs2io90l08kqb1od8lcg.databases.appdomain.cloud;PORT=30120;SECURITY=SSL;UID=gyq42313;PWD=TRn8xYTPTGloNwQC;", "", "")

load_dotenv()   #load keys from .env
sg = sendgrid.SendGridAPIClient(api_key = os.environ.get('SENDGRID_API_KEY'))   #set SendGrid API Key
from_email = Email("dhanushcodepro@gmail.com")     #the address that sends emails to the users



@app.route('/')
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('signin'))  #ask user to sign in if not done already

    return render_template('dashboard.html', pred=session['username'])  #go to homepage if signed in




@app.route('/signout')
def signout():
    session.pop('username', None)   #remove user session upon signing out
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
    if 'username' in session:   #inform user if they're already signed in the same session
        flash('You are already signed in! Sign out to login with a different account')
        return redirect(url_for('dashboard'))
    return render_template('login.html')   #take user to the sign in page




@app.route('/signinform', methods=['POST'])
def signinform():
    uid = request.form['email']   #get user id and password from the form
    pwd = request.form['pass']
    print(uid,pwd)
    sql = 'SELECT * from users WHERE email=? AND password=?' #check user credentials in the database
    pstmt = ibm_db.prepare(connection, sql)
    ibm_db.bind_param(pstmt, 1, uid)
    ibm_db.bind_param(pstmt, 2, pwd)
    ibm_db.execute(pstmt)

    acc = ibm_db.fetch_assoc(pstmt)
    
    if acc: #if the user is already registered to the application
        session['username'] = acc['USERNAME']
        flash('Signed in successfully!')
        return redirect(url_for('dashboard'))
        
    else:   #warn upon entering incorrect credentials
        flash('Incorrect credentials. Please try again!')
        return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)