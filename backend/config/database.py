import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy

# Load values from backend/.env so they are available via os.getenv.
load_dotenv()

# Shared SQLAlchemy instance. Bound to the Flask app in init_db().
db = SQLAlchemy()


def get_database_uri():
    """Build a MySQL connection URL using the PyMySQL driver."""
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3306")
    name = os.getenv("DB_NAME", "git_graveyard")
    user = os.getenv("DB_USER", "root")
    password = quote_plus(os.getenv("DB_PASSWORD", ""))

    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"


def init_db(app):
    """Attach SQLAlchemy to the Flask app. Does not create tables."""
    app.config["SQLALCHEMY_DATABASE_URI"] = get_database_uri()
    db.init_app(app)
