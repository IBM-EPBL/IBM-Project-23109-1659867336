from flask import Flask, render_template

flask = Flask(__name__)

@flask.route("/")
def home():
    return render_template('home.html')

@flask.route("/register")
def register():
    return render_template('register.html')

@flask.route("/login")
def login():
    return render_template('log_in.html')

@flask.route("/about")
def about():
    return render_template('about.html')
