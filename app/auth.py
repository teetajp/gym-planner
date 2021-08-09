""" Handles the authentication system """
from flask import (
    Blueprint,
    flash,
    redirect,
    request,
    session,
    render_template,
)
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required
from db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/register", methods=["GET", "POST"])
def register():
    """Registers a user

    Validates that username and email is not already taken. Hashes the password
    for security.
    """
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        db = get_db()
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


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    session.clear()

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        db = get_db()

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


@bp.route("/logout")
def logout():
    """Log user out"""

    session.clear()

    return redirect("/")


@bp.route("/change_pw", methods=["GET", "POST"])
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
        db = get_db()
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
