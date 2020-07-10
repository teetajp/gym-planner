from flask import Flask
from helpers import apology, login_required

app = Flask(__name__)

@app.route('/')
def index():
    return 'Index Page'

@app.route('/user_login')
def user_login():
    """Log user in"""
    return 'Users can login here'

@app.route('/coach_login')
def coach_login():
    """Log coach in"""
    return 'Coaches can login here'

@app.route('/register')
def register():
    """Allow coaches and users to register an account"""
    return 'TODO'