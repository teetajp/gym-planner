venv/Scripts/Activate.ps1
$env:DATABASE_URL = "postgres://$(whoami)"
$env:FLASK_APP = "main.py"
$env:FLASK_ENV = "development"
flask run