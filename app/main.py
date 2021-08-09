""" Runs the Flask server """
import os
from tempfile import mkdtemp

from flask import (
    Flask,
    render_template,
    send_from_directory,
)
from flask_session import Session
from werkzeug.exceptions import default_exceptions, HTTPException, \
    InternalServerError

import auth
import planner
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

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

app.register_blueprint(auth.bp)
app.register_blueprint(planner.bp)
Session(app)


@app.route("/")
@login_required
def index():
    return render_template("index.html")



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
    print(e)
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

if __name__ == "__main__":
    app.run()
