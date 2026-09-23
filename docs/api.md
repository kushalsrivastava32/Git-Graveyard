# Git Graveyard — Backend API Contract (v1)

This document is the frozen contract between the backend and any
consumer (frontend, scripts, integrations). It describes every
request shape, response field, and error status the backend currently
supports.

Status: v1 — rule-based classification. Not yet ML.
Stability: Fields marked STABLE are stable and will not be removed in v2.
Fields marked CHANGING may change in v2 (see "v2 roadmap" at the bottom).

---

## 1. Endpoint

POST /api/repository/analyze
Content-Type: application/json

Accepts either a local repository path or a GitHub URL.
Exactly one of `path` or `url` must be present in the request body.

---

## 2. Request shapes

### 2.1 Local path

{
    "path": "D:\\Git Graveyard\\Git-Graveyard"
}

- `path` must be a non-empty string.
- Must point to a directory containing a valid `.git` folder.

### 2.2 GitHub URL

{
    "url": "https://github.com/kushalsrivastava32/Git-Graveyard"
}

Supported formats:
- https://github.com/owner/repo
- https://github.com/owner/repo.git
- https://github.com/owner/repo/tree/main
- git@github.com:owner/repo.git
- owner/repo

Scope: Public repositories only in v1. Private repos require a
GITHUB_TOKEN environment variable on the server (not yet exposed
to clients).

---

## 3. Success response — 200 OK

The response is a single JSON object with six top-level keys:

{
    "repository":      { ... },
    "commits":         { ... },
    "files":           { ... },
    "file_activity":   [ ... ],
    "activity":        [ ... ],
    "graveyard":       [ ... ]
}

### 3.1 repository  [STABLE]

Repository-level summary.

{
    "name": "Git-Graveyard",
    "path": "D:\\Git Graveyard\\Git-Graveyard",
    "current_branch": "main",
    "total_commits": 6,
    "latest_commit": {
        "hash": "c3e9b449fb5546255c336dd36dfaf1a65b9457a9",
        "author_name": "Kushal Srivastava",
        "author_email": "kushalsrivastava32@gmail.com",
        "date": "2026-09-13T15:50:17+05:30",
        "message": "Restore clean error handling..."
    },
    "repository_days_since_last_commit": 9
}

Note: For GitHub sources, `name` is the real repository name
(not the temporary clone folder name).

### 3.2 commits  [STABLE]

Commit-history aggregates.

{
    "total_commits": 6,
    "first_commit":  { ...same shape as latest_commit... },
    "latest_commit": { ... },
    "recent_commits": [ ...last 10, newest first... ],
    "contributors": {
        "total_contributors": 1,
        "details": [
            { "name": "...", "email": "...", "commit_count": 6 }
        ]
    },
    "commit_activity": {
        "commits_by_year":  { "2026": 6 },
        "commits_by_month": { "2026-09": 6 }
    }
}

### 3.3 files  [STABLE]

Current file-tree summary.

{
    "total_files": 23,
    "total_size_bytes": 149510,
    "files_by_extension": {
        ".py": 17, ".html": 1, ".css": 1, ".js": 1, ".png": 1, ".txt": 1,
        "other": 1
    },
    "largest_files": [
        { "path": "frontend/logo.png", "size_bytes": 103221 }
    ]
}

### 3.4 file_activity  [STABLE]

Per-file raw metrics (no classification).

[
    {
        "path": "backend/app.py",
        "commit_count": 2,
        "first_modified": "2026-09-10T15:14:22+05:30",
        "last_modified":  "2026-09-13T15:50:17+05:30"
    }
]

### 3.5 activity  [STABLE]

Same as file_activity, plus computed metrics and a naive
recommendation string. Kept for convenience; the authoritative
classification lives in `graveyard`.

[
    {
        "path": "backend/app.py",
        "commit_count": 2,
        "first_modified": "2026-09-10T15:14:22+05:30",
        "last_modified":  "2026-09-13T15:50:17+05:30",
        "days_since_last_modified": 9,
        "file_age_days": 12,
        "recommendation": "active"
    }
]

### 3.6 graveyard  [STABLE] — the ranked result

This is the primary output. A list of every tracked file, each
scored for potential abandonment and sorted by `staleness_score`
descending (highest = most suspicious first).

[
    {
        "path": "backend/app.py",
        "commit_count": 2,
        "days_since_last_modified": 9,
        "file_age_days": 12,
        "staleness_score": 6,
        "classification": "healthy",
        "signals": {
            "inactivity": 0.0,
            "historical": 0.2,
            "repo_multiplier": 1.0
        }
    }
]

Field reference:

Field                     Type          Meaning
------------------------  ------------  -------------------------------------------
path                      string        Path relative to the repo root
commit_count              int           Number of commits that touched this file
days_since_last_modified  int or null   Days since the most recent commit
file_age_days             int or null   Days since the first commit
staleness_score           int, 0-100    Composite score. CHANGING in v2.
classification            string        Bucketed verdict. STABLE.
signals                   object        Contributing sub-scores. Shape may extend in v2.

Classification buckets  [STABLE]

Value                     Score range   Meaning
------------------------  ------------  ------------------------------------------
healthy                   0-29          Recently touched, actively used
inactive                  30-59         Hasn't changed recently, no strong signal
suspicious                60-79         Likely abandoned; worth reviewing
potentially_abandoned     80-100        Strong evidence of abandonment

Consumers should display `classification`, not `staleness_score`.
The score is a moving internal number; the classification is the
user-facing verdict.

signals object  [CHANGING]

Currently contains:

Key                Range      Meaning
-----------------  ---------  ------------------------------------------
inactivity         0.0-1.0    How long since last modification
historical         0.0-1.0    Commit count x inactivity pattern
repo_multiplier    0.4-1.0    Amplifier based on overall repo activity

In v2, additional keys may be added (e.g., dependency, content).
Existing keys will not be removed, but their values may be recomputed.

---

## 4. Error responses

The endpoint returns one of the following error statuses. Every
error body is { "error": "<human-readable message>" }.

Status                    When                                       Example message
------------------------  -----------------------------------------  ----------------------------------------------------------
400 Bad Request           Missing/invalid path/url; bad URL          "Provide either 'path' (local) or 'url' (GitHub)."
400 Bad Request           Body is not valid JSON                     "Request body must be valid JSON."
404 Not Found             Local path does not exist                  "Path does not exist: D:\\nope"
413 Payload Too Large     GitHub repo exceeds size limit (reserved)  —
422 Unprocessable Entity  Path exists but is not a Git repository    "Path is not a Git repository: ..."
500 Internal Server Error Unexpected backend failure                 "An unexpected error occurred while analyzing the repository."
502 Bad Gateway           GitHub clone failed (auth, network, 404)   "Failed to clone owner/repo: ..."

---

## 5. Example: minimal frontend flow

const res = await fetch("/api/repository/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url: "https://github.com/owner/repo" })
});

if (!res.ok) {
    const err = await res.json();
    showError(err.error);
    return;
}

const data = await res.json();

// Show the graveyard ranked list
data.graveyard.forEach(file => {
    renderFile(file.path, file.classification, file.staleness_score);
});

---

## 6. What is NOT in v1

Explicitly out of scope for this version:

- Authentication (no user accounts, no tokens from clients)
- Persistence (no database writes; every request re-analyzes)
- Deletion, PR creation, or any write action to any repository
- ML-based classification (rule-based only)
- Dependency analysis or content analysis
- Private GitHub repos (unless GITHUB_TOKEN is set server-side)

---

## 7. v2 roadmap (informational — do not build against this yet)

The backend will evolve. Planned additions:

- New signals keys: dependency (whether other files reference
  this one), content (deprecated APIs, TODO markers).
- Recalculated staleness_score once the new signals are in.
- New optional response fields (additions only — existing fields
  stay).
- Persistence layer so analyses can be stored and compared over
  time.
- ML classification replacing the rule-based score once labeled
  data is available.

Guarantee for consumers: classification and all top-level
response keys (repository, commits, files, file_activity,
activity, graveyard) will remain stable across v2. New fields
may be added; none will be removed.

---

## 8. Questions / changes

If you need a new field or a shape change, request it from the
backend owner before building against it. Don't guess.