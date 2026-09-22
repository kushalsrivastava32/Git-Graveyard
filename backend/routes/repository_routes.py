import re

from flask import Blueprint, jsonify, request

from git_analysis.repository_analyzer import (
    NotAGitRepositoryError,
    PathNotFoundError,
)
from services.repository_service import RepositoryService
from services.providers import GitHubRepositoryProvider
from services.providers.github_provider import (
    GitHubCloneError,
    GitHubRepoTooLargeError,
)

repository_bp = Blueprint(
    "repository", __name__, url_prefix="/api/repository"
)
repository_service = RepositoryService()


# ---------------------------------------------------------------------
# URL parsing helper
# ---------------------------------------------------------------------

def parse_repo_url(url):
    """
    Normalize various GitHub URL formats to (owner, repo).

    Handles:
        https://github.com/owner/repo
        https://github.com/owner/repo.git
        https://github.com/owner/repo/tree/main
        git@github.com:owner/repo.git
        owner/repo
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string.")

    s = url.strip()

    # SSH: git@github.com:owner/repo.git
    m = re.match(r"^git@github\.com:([\w.-]+)/([\w.-]+?)(?:\.git)?/?$", s)
    if m:
        return m.group(1), m.group(2)

    # Strip scheme + www + github.com
    s = re.sub(r"^(https?://)?(www\.)?github\.com/", "", s)

    # HTTPS or bare slug
    m = re.match(r"^([\w.-]+)/([\w.-]+?)(?:\.git)?(?:/.*)?$", s)
    if m:
        return m.group(1), m.group(2)

    raise ValueError(f"Could not parse GitHub URL: {url}")


# ---------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------

@repository_bp.route("/analyze", methods=["POST"])
def analyze_repository():
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    # -----------------------------------------------------------------
    # GitHub URL branch
    # -----------------------------------------------------------------
    if "url" in data:
        try:
            owner, repo = parse_repo_url(data["url"])
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

        try:
            provider = GitHubRepositoryProvider(owner, repo)
            result = repository_service.analyze_repository(provider)
            return jsonify(result), 200

        except GitHubRepoTooLargeError as error:
            return jsonify({"error": str(error)}), 413

        except GitHubCloneError as error:
            return jsonify({"error": str(error)}), 502

        except Exception:
            import traceback
            traceback.print_exc()
            return jsonify({
                "error": (
                    "An unexpected error occurred while analyzing "
                    "the repository."
                )
            }), 500

    # -----------------------------------------------------------------
    # Local path branch (unchanged from your current version)
    # -----------------------------------------------------------------
    if "path" not in data:
        return jsonify({
            "error": "Provide either 'path' (local) or 'url' (GitHub)."
        }), 400

    path = data["path"]
    if not isinstance(path, str) or not path.strip():
        return jsonify({"error": "path must be a non-empty string."}), 400

    try:
        result = repository_service.analyze_repository(path.strip())
        return jsonify(result), 200

    except PathNotFoundError as error:
        return jsonify({"error": str(error)}), 404

    except FileNotFoundError as error:
        return jsonify({"error": str(error)}), 404

    except NotAGitRepositoryError as error:
        return jsonify({"error": str(error)}), 422

    except Exception:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": (
                "An unexpected error occurred while analyzing "
                "the repository."
            )
        }), 500