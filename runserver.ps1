venv/Scripts/Activate.ps1
$env:FLASK_APP = "app/main.py"
$env:FLASK_ENV = "development"
flask run