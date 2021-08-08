"""
Runs the Flask server
"""
import os
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    send_from_directory,
)
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, \
    InternalServerError
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


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for user's hashed password
        hashed_pw = db.execute(
            "SELECT hash FROM users WHERE username = :username",
            {"username": request.form.get("username")}).fetchall()

        if len(hashed_pw) != 1:
            return apology("Duplicate users found")
        elif not check_password_hash(hashed_pw[0][0],
                                     request.form.get("password")):
            return apology("invalid username and/or password", 403)

        print(len(hashed_pw))

        # Remember which user has logged in
        session["username"] = request.form.get("username")

        # Redirect user to home page
        flash("Login successful!")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
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
        elif len(db.execute(
                "SELECT user_id FROM users WHERE username = :username",
                {"username": request.form.get("username")}).fetchall()) != 0:
            return apology("username already exists", 403)

        # Ensure email was submitted
        if not request.form.get("email"):
            return apology("must provide email", 403)

        # Ensure email does not already exist
        elif len(db.execute("SELECT user_id FROM users WHERE email = :email",
                            {"email": request.form.get(
                                "email")}).fetchall()) != 0:
            return apology("email already exists", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Ensure password and confirmation matches
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 403)

        # TODO: Add regex filter to sanitize email inputs

        # Insert the new user into users table
        db.execute(
            "INSERT INTO users (username, hash, email) VALUES (:username, "
            ":hash, :email)",
            {"username": request.form.get("username"),
             "hash": generate_password_hash(request.form.get("password")),
             "email": request.form.get("email")})
        print("Added user with username: " + request.form.get("username") +
              " and email: " + request.form.get("email"))
        db.commit()

        # Log registered user in and remember the id
        session["username"] = request.form.get("username")

        # Previously remember session by user_id
        # session["user_id"] = db.execute("SELECT user_id FROM users WHERE
        # username = :username",
        #                                 {"username": request.form.get(
        #                                 "username")}).fetchall()[0]

        # Redirect user to home page
        flash("Registration successful. Automatically logged in.")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/change_pw", methods=["GET", "POST"])
@login_required
def change_pw():
    """Allow user to change password"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure current password was submitted
        if not request.form.get("current_pw"):
            return apology("must provide current password", 403)

        elif not request.form.get("new_pw"):
            return apology("must provide new password", 403)

        elif request.form.get("new_pw") != request.form.get("confirm_pw"):
            # Ensure password and confirmation matches
            return apology("new password does not match confirmation password",
                           403)

        elif request.form.get("current_pw") == request.form.get("new_pw"):
            return apology("new password must not match current password", 403)

        # Query database for the user's hashed password
        result = db.execute(
            "SELECT user_id, hash FROM users WHERE username = :username",
            {"username": session["username"]}).fetchall()

        user_id = result[0][0]
        hashed_pw = result[0][1]
        print(user_id)
        print(hashed_pw)

        # Ensure user exists and submitted password matches password in
        # database
        if len(result) != 1:
            return apology("duplicate users found", 403)
        elif not check_password_hash(hashed_pw,
                                     request.form.get("current_pw")):
            return apology("inputted password must not match current password",
                           403)

        db.execute("UPDATE users SET hash = :hash WHERE user_id = :user_id",
                   {"hash": generate_password_hash(request.form.get("new_pw")),
                    "user_id": user_id})
        db.commit()

        flash("Password changed successfully.")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("change_pw.html")


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
