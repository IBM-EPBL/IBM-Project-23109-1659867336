from flask import Flask, render_template

# Instantiate flash app
app = Flask(__name__)

# Here we are creating route for pages
# Later we will move to separate routes/views modules while connecting to the database

@app.route("/")
def home():
    return render_template('home.html')

@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/signin")
def sign_in():
    return render_template('sign_in.html')

@app.route("/signup")
def sign_up():
    return render_template('sign_up.html')
