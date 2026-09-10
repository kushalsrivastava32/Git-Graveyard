from flask import Blueprint, jsonify, request

from git_analysis.repository_analyzer import NotAGitRepositoryError, PathNotFoundError
from services.repository_service import RepositoryService

repository_bp = Blueprint("repository", __name__, url_prefix="/api/repository")
repository_service = RepositoryService()


@repository_bp.route("/analyze", methods=["POST"])
def analyze_repository():
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    if "path" not in data:
        return jsonify({"error": "Missing required field: path"}), 400

    path = data["path"]
    if not isinstance(path, str) or not path.strip():
        return jsonify({"error": "path must be a non-empty string."}), 400

    try:
        result = repository_service.analyze_repository(path.strip())
        return jsonify(result), 200
    except PathNotFoundError as error:
        return jsonify({"error": str(error)}), 404
    except NotAGitRepositoryError as error:
        return jsonify({"error": str(error)}), 422
    except Exception:
        return jsonify(
            {"error": "An unexpected error occurred while analyzing the repository."}
        ), 500
