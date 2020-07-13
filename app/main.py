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

app.secret_key = os.getenv("SECRET_KEY")

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

# TODO: SANITIZE ALL user inputs

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

        # Query database for username
        users = db.execute("SELECT user_id, hash FROM users WHERE username = :username",
                          {"username": request.form.get("username")}).fetchall()

        # Ensure username exists
        if len(users) != 1:
            return apology("invalid username and/or password", 403)

        # Ensure submitted password matches password in database
        for user_id, hash in users:
            if not check_password_hash(hash, request.form.get("password")):
                return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = user_id
        session["username"] = request.form.get("username")
        print("User with user_id: " + str(session["user_id"]) +" has logged in.")

        # Redirect user to home page
        flash("Login successful!")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    print("User with user_id: " + str(session["user_id"]) + " has logged out.")

    # Forget any user_id
    session.clear()
    
    # Redirect user to login form
    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Allow coaches and users to register an account"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure username does not already exist
        elif len(db.execute("SELECT user_id FROM users WHERE username = :username",
                          {"username": request.form.get("username")}).fetchall()) != 0:
            return apology("username already exists", 403)

        # Ensure username does not already exist
        elif len(db.execute("SELECT user_id FROM users WHERE username = :username",
                        {"username": request.form.get("email")}).fetchall()) != 0:
            return apology("email already exists", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Ensure password and confirmation matches
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 403)

        # TODO: Add regex filter to sanitize email inputs

        # Insert the new user into users table
        db.execute("INSERT INTO users (username, hash, email) VALUES (:username, :hash, :email)",
            {"username": request.form.get("username"),
            "hash": generate_password_hash(request.form.get("password")),
            "email": request.form.get("email")})
        db.commit()

        print(f"Added user with username: " + request.form.get("username") +
        " and email: " + request.form.get("email"))

        # Log registered user in and remember the user_id and username
        session["user_id"] = db.execute("SELECT user_id FROM users WHERE username = :username",
                          {"username": request.form.get("username")}).fetchall()[0]
        session["username"] = request.form.get("username")

        print("User with user_id: " + str(session["user_id"]) + " has logged in.")

        # Redirect user to home page
        flash("Registration successful. Automatically logged in.")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/password", methods=["GET", "POST"])
@login_required
def change_password():
    """Allow user to change password"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure user submitted all fields
        if not request.form.get("current_pw"):
            return apology("Missing current password", 400)

        elif not request.form.get("new_pw"):
            return apology("Missing new password", 400)

        elif not request.form.get("confirm_pw"):
            return apology("Missing password confirmation", 400)

        # Ensure new password matches the password confirmation
        elif (request.form.get("new_pw") != request.form.get("confirm_pw")):
            return apology("New password does not match password confirmation", 400)

        # Query username table for hashed password
        results = db.execute("SELECT hash FROM users WHERE user_id = :user_id",
            {"user_id": session["user_id"]}).fetchall()
        
        # Ensure submitted current_password hash matches the password in the database
        if not check_password_hash(results[0][0], request.form.get("current_pw")):
            return apology("Submitted password is incorrect", 400)

        else:
            # Update hashed password in the database to the new one
            db.execute("UPDATE users SET hash = :hash WHERE user_id = :user_id",
                        {"hash": generate_password_hash(request.form.get("new_pw")),
                        "user_id": session["user_id"]})
            db.commit()

        # Redirect user to home page
        flash("Password changed succesfully!")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("password.html")

@app.route("/invite_coach", methods=["GET", "POST"])
@login_required
def invite_coach():
    """Allow user to invite coaches"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        # TODO: Check to see if invited coach has a coach_id already;
        # if not, create one.
        if not request.form.get("coach_email"):
            return apology("Need coach email address", 400)

        # Look up all coaches that the user invited
        coaches = db.execute("SELECT username, email FROM users JOIN coaches ON users.user_id = coaches.user_id \
            JOIN coach_users ON coach_users.coach_id = coaches.coach_id WHERE coach_users.user_id = :user_id",
            {"user_id": session["user_id"]}).fetchall()

        # Let user invite coach even if coach has not created account using email, but alert them

        # Ask user if coach's username is correct

        # What happens if insert into table with already existing data?

        # TODO: INSERT INTO coach_users

        # TODO: remove coach with red 'remove button'
        # Use JS? or do we have to use Flask?

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:

        # Look up all coaches that the user invited and return it to the user
        coaches = db.execute("SELECT username, email FROM users JOIN coaches ON users.user_id = coaches.user_id \
            JOIN coach_users ON coach_users.coach_id = coaches.coach_id WHERE coach_users.user_id = :user_id",
            {"user_id": session["user_id"]}).fetchall()

        for coach in coaches:
            print(coach[0])
            print(coach[1])
        return render_template("invite_coach.html", coaches=coaches)

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


# Template for Adding Page
# @app.route("/<ADD PAGE NAME>", methods=["GET", "POST"])
# @login_required
# def <FUNCTION_NAME>():
#     """Allow user to change password"""

#     # User reached route via POST (as by submitting a form via POST)
#     if request.method == "POST":

#         # Redirect user to home page
#         return redirect("/")

#     # User reached route via GET (as by clicking a link or via redirect)
#     else:
#         return render_template("<TEMPLATE NAME>.html")