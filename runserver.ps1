venv\Scripts\activate.ps1
$env:FLASK_APP="application.py"
$env:FLASK_ENV="development"
flask run --host=0.0.0.0