import os
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for, send_from_directory
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route('/')
def index():
    return render_template("index.html")

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

@app.route('/favicon.ico') 
def favicon(): 
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ = '__main__':
    app.run()