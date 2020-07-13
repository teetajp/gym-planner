import os
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
    send_from_directory,
)
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
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
    
# Make sure DATABASE_URL key is set
if not os.environ.get("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL not set")

# Connect to PostgreSQL database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/")
@login_required
def index():
    return render_template("layout.html")


@app.route("/login")
def login():
    """Log user and/or coach in"""
    return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Allow coaches and users to register an account"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure username does not already exist
        elif len(db.execute("SELECT * FROM users WHERE username = :username",
                          {"username": request.form.get("username")})) != 0:
            return apology("username already exists", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Ensure password and confirmation matches
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 403)


        # Add filter for 
        # Insert the new user into users table
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
            {"username": request.form.get("username"),
            "hash": generate_password_hash(request.form.get("password"))})

        # Redirect user to home page
        flash("Registration successful. Please login.")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/change_pw", methods=["GET", "POST"])
@login_required
def change_pw():
    """Allow user to change password"""

    return "TODO"


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    # return apology(e.name, e.code)
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

if __name__ == "__main__":
    app.run()

