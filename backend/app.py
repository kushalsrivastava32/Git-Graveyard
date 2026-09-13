import os

from flask import Flask, jsonify, send_from_directory
from dotenv import load_dotenv

from config.database import init_db
from routes.repository_routes import repository_bp

load_dotenv()

app = Flask(__name__)
init_db(app)
app.register_blueprint(repository_bp)


@app.route("/")
def health():
    """Simple health check so hitting the root gives useful JSON."""
    return jsonify({
        "message": "Git Graveyard backend is running",
        "endpoints": {
            "frontend": "/app",
            "analyze": "POST /api/repository/analyze",
        },
    })


@app.route("/app")
@app.route("/app/<path:filename>")
def frontend(filename="index.html"):
    frontend_folder = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "frontend",
    )
    return send_from_directory(frontend_folder, filename)


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)