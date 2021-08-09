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


@app.route("/register", methods=["GET", "POST"])
def register():
    """Registers a user

    Validates that username and email is not already taken. Hashes the password
    for security.
    """
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        error = None

        # Ensure username, email, and password are submitted and do not match.
        if not username:
            error = "must provide username"
        elif not email:
            error = "must provide email"
        elif not password:
            error = "must provide password"
        elif (db.execute(
                "SELECT user_id FROM users WHERE username = :username",
                {"username": request.form.get(
                    "username")}).fetchone() is not None):
            error = "username already exists"
        elif (db.execute("SELECT user_id FROM users WHERE email = :email",
                         {"email": request.form.get(
                             "email")}).fetchall() is not None):
            error = "email already exists"
        elif request.form.get("password") != request.form.get("confirmation"):
            error = "passwords do not match"

        if error is not None:
            return apology(error, 403)

        # Insert the new user into the database
        db.execute(
            "INSERT INTO users (username, hash, email) VALUES (:username, "
            ":hash, :email)",
            {"username": request.form.get("username"),
             "hash": generate_password_hash(request.form.get("password")),
             "email": request.form.get("email")})
        db.commit()

        # Log registered user in and remember the id
        session["username"] = request.form.get("username")

        flash("Registration successful. Automatically logged in.")
        return redirect("/")

    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    session.clear()

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if not username:
            return apology("must provide username", 403)
        elif not password:
            return apology("must provide password", 403)

        # Query database for user's hashed password
        hashed_pw = db.execute(
            "SELECT hash FROM users WHERE username = :username",
            {"username": request.form.get("username")}).fetchone()

        if hashed_pw is None or not check_password_hash(hashed_pw[0],
                                                        request.form.get(
                                                            "password")):
            return apology("invalid username and/or password", 403)

        session["username"] = request.form.get("username")

        flash("Login successful!")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    session.clear()

    return redirect("/")


@app.route("/change_pw", methods=["GET", "POST"])
@login_required
def change_pw():
    """Allow user to change password"""

    if request.method == "POST":
        current_pw = request.form.get("current_pw")
        new_pw = request.form.get("new_pw")
        confirm_pw = request.form.get("confirm_pw")
        error = None

        if not current_pw:
            error = "must provide current password"
        elif not new_pw:
            error = "must provide new password"
        elif new_pw != confirm_pw:
            error = "new password does not match confirmation password"
        elif current_pw == new_pw:
            error = "new password must not match current password"

        if error is not None:
            return apology(error, 403)

        # Query database for the user's hashed password
        result = db.execute(
            "SELECT user_id, hash FROM users WHERE username = :username",
            {"username": session["username"]}).fetchone()

        user_id = result[0]
        hashed_pw = result[1]

        # Ensure user's submitted password matches actual password
        if not check_password_hash(hashed_pw, current_pw):
            return apology(
                "submitted password must not match current password", 403)

        db.execute("UPDATE users SET hash = :hash WHERE user_id = :user_id",
                   {"hash": generate_password_hash(request.form.get("new_pw")),
                    "user_id": user_id})
        db.commit()

        flash("Password changed successfully.")
        return redirect("/")

    else:
        return render_template("change_pw.html")


@app.route("/plans", methods=["GET", "POST"])
@login_required
def workout_plans():
    return render_template("plans.html")


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
