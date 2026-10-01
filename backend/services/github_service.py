import os
import re
import base64
import requests
from typing import Dict, Any, List, Tuple, Optional
from dotenv import load_dotenv

load_dotenv()

# Common web/reserved paths on github.com that are not user repositories
GITHUB_RESERVED_ROOTS = {
    "settings", "pricing", "features", "marketplace", "pulls", "issues",
    "explore", "trending", "collections", "events", "about", "contact",
    "security", "login", "join", "enterprise", "team", "topics", "search"
}

def parse_github_url(url: str) -> Dict[str, Any]:
    """
    Safely parses and validates a GitHub repository URL.
    Accepts formats like:
      - https://github.com/owner/repository
      - https://github.com/owner/repository.git
      - http://github.com/owner/repository/
      - github.com/owner/repository
      - https://github.com/owner/repository/tree/main/...
    Returns:
      {
        "valid": True/False,
        "owner": str or None,
        "repo": str or None,
        "normalized_url": str or None,
        "error": str or None
      }
    """
    cleaned = (url or "").strip()
    if not cleaned:
        return {"valid": False, "owner": None, "repo": None, "normalized_url": None, "error": "No GitHub URL was provided."}

    # Normalize protocol
    if not (cleaned.startswith("http://") or cleaned.startswith("https://")):
        cleaned = "https://" + cleaned

    # Match github.com URL structure
    # Owner: alphanumeric or hyphen (not beginning/ending with hyphen)
    # Repo: alphanumeric, hyphen, underscore, period
    pattern = re.compile(
        r"^https?://(?:www\.)?github\.com/([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+)(?:/.*)?$",
        re.IGNORECASE
    )
    match = pattern.match(cleaned)
    if not match:
        return {
            "valid": False,
            "owner": None,
            "repo": None,
            "normalized_url": None,
            "error": "Invalid GitHub repository URL. Must be in the format: https://github.com/owner/repository"
        }

    owner = match.group(1).strip()
    repo = match.group(2).strip()

    # Clean off trailing .git if present
    if repo.endswith(".git"):
        repo = repo[:-4]

    # Check reserved paths
    if owner.lower() in GITHUB_RESERVED_ROOTS or not repo:
        return {
            "valid": False,
            "owner": None,
            "repo": None,
            "normalized_url": None,
            "error": f"'{owner}' is a reserved GitHub path, not a valid repository owner."
        }

    normalized = f"https://github.com/{owner}/{repo}"
    return {
        "valid": True,
        "owner": owner,
        "repo": repo,
        "normalized_url": normalized,
        "error": None
    }

def get_github_headers() -> Dict[str, str]:
    """
    Prepares GitHub API request headers.
    Supports optional GITHUB_TOKEN from environment.
    Never prints or leaks the token.
    """
    token = os.getenv("GITHUB_TOKEN", "").strip()
    headers = {
        "User-Agent": "ProofHire-Evidence-Inspector/1.0 (ProofHire AI Candidate Intelligence Bot)",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

def fetch_github_repository(owner: str, repo: str) -> Dict[str, Any]:
    """
    Retrieves public repository information using the official GitHub REST API.
    Does NOT scrape HTML.
    
    Retrieves:
      - Repository metadata (name, description, default branch, primary language, topics, stars, forks)
      - Language byte distribution
      - README content (base64 decoded)
      - Repository file/tree structure
      - Recent commit metadata
      - Contributors metadata
      
    Handles:
      - 404 (Not found or private)
      - 403 / 429 (Rate limit)
      - Empty repositories
      - Missing README
    """
    base_api = f"https://api.github.com/repos/{owner}/{repo}"
    headers = get_github_headers()
    auth_mode = "Authenticated (GITHUB_TOKEN)" if "Authorization" in headers else "Public Unauthenticated"
    
    result = {
        "success": False,
        "status": "retrieval_failed",
        "auth_mode": auth_mode,
        "owner": owner,
        "repo": repo,
        "repository_name": repo,
        "repository_url": f"https://github.com/{owner}/{repo}",
        "description": None,
        "default_branch": "main",
        "primary_language": None,
        "languages": {},
        "topics": [],
        "readme_summary": None,
        "readme_full": None,
        "repository_structure": [],
        "file_tree": [],
        "recent_commits": [],
        "contributors": [],
        "is_empty": False,
        "error": None,
        "error_type": None
    }

    session = requests.Session()

    # 1. Fetch Repository Metadata
    try:
        res = session.get(base_api, headers=headers, timeout=8)
        if res.status_code == 404:
            result["error"] = f"Repository '{owner}/{repo}' not found on GitHub or is private."
            result["error_type"] = "not_found"
            return result
        elif res.status_code in (403, 429):
            is_rate_limit = (
                res.headers.get("X-RateLimit-Remaining") == "0" or
                "rate limit" in res.text.lower()
            )
            if is_rate_limit:
                result["error"] = "GitHub API rate limit exceeded. Please configure GITHUB_TOKEN in backend/.env or wait before trying again."
                result["error_type"] = "rate_limited"
            else:
                result["error"] = f"GitHub API access forbidden: {res.json().get('message', 'Forbidden')}"
                result["error_type"] = "forbidden"
            return result
        elif res.status_code != 200:
            result["error"] = f"GitHub API returned HTTP status {res.status_code}."
            result["error_type"] = "api_error"
            return result

        meta = res.json()
        result["repository_name"] = meta.get("name", repo)
        result["description"] = meta.get("description")
        result["repository_url"] = meta.get("html_url", result["repository_url"])
        default_branch = meta.get("default_branch") or "main"
        result["default_branch"] = default_branch
        result["primary_language"] = meta.get("language")
        result["topics"] = meta.get("topics", [])
        result["stars"] = meta.get("stargazers_count", 0)
        result["forks"] = meta.get("forks_count", 0)
        result["is_empty"] = meta.get("size", 0) == 0

    except requests.exceptions.RequestException as e:
        result["error"] = f"Network error connecting to GitHub API: {str(e)}"
        result["error_type"] = "network_error"
        return result

    # 2. Fetch Language Distribution
    try:
        lang_res = session.get(f"{base_api}/languages", headers=headers, timeout=6)
        if lang_res.status_code == 200:
            result["languages"] = lang_res.json()
    except Exception:
        pass

    # 3. Fetch README
    try:
        readme_res = session.get(f"{base_api}/readme", headers=headers, timeout=6)
        if readme_res.status_code == 200:
            readme_data = readme_res.json()
            content_encoded = readme_data.get("content", "")
            if content_encoded:
                try:
                    decoded = base64.b64decode(content_encoded).decode("utf-8", errors="replace").strip()
                    result["readme_full"] = decoded[:4000] # Safe upper cap
                    # Create clean excerpt/summary
                    lines = [ln.strip() for ln in decoded.splitlines() if ln.strip()]
                    summary_lines = []
                    for line in lines[:25]:
                        # Skip pure badge lines
                        if re.match(r"^\[!\[.*\]\(.*\)\]\(.*\)$", line) or re.match(r"^!\[.*\]\(.*\)$", line):
                            continue
                        summary_lines.append(line)
                        if len("\n".join(summary_lines)) > 800:
                            break
                    result["readme_summary"] = "\n".join(summary_lines[:15]) if summary_lines else decoded[:500]
                except Exception:
                    result["readme_summary"] = "README was present but could not be parsed as text."
        elif readme_res.status_code == 404:
            result["readme_summary"] = "README unavailable in this repository."
    except Exception:
        result["readme_summary"] = "README unavailable."

    # 4. Fetch Repository File Tree Structure
    file_tree = []
    detected_structure = []
    manifest_contents = {}

    try:
        tree_res = session.get(f"{base_api}/git/trees/{result['default_branch']}?recursive=1", headers=headers, timeout=8)
        if tree_res.status_code == 200:
            tree_data = tree_res.json()
            raw_tree = tree_data.get("tree", [])
            for item in raw_tree:
                p = item.get("path", "")
                t = item.get("type", "")
                if t == "blob":
                    file_tree.append(p)
                elif t == "tree":
                    # Record directory
                    if "/" not in p or p.count("/") <= 2:
                        detected_structure.append(f"{p}/")
        elif tree_res.status_code in (404, 409):
            # Fallback to contents API
            contents_res = session.get(f"{base_api}/contents", headers=headers, timeout=6)
            if contents_res.status_code == 200:
                for item in contents_res.json():
                    name = item.get("name", "")
                    t = item.get("type", "")
                    if t == "dir":
                        detected_structure.append(f"{name}/")
                    else:
                        file_tree.append(name)
    except Exception:
        pass

    # Extract top-level key directory names if detected_structure is empty or sparse
    if not detected_structure and file_tree:
        top_dirs = set()
        for f in file_tree:
            parts = f.split("/")
            if len(parts) > 1:
                top_dirs.add(f"{parts[0]}/")
        detected_structure = sorted(list(top_dirs))[:15]

    result["file_tree"] = file_tree[:200]
    result["repository_structure"] = detected_structure[:20]

    # Optional: fetch small manifest files (requirements.txt or package.json) if present in root
    # This guarantees deterministic skill signal extraction with zero ambiguity
    for manifest_name in ["requirements.txt", "package.json", "pyproject.toml", "Dockerfile"]:
        if manifest_name in file_tree or any(f.endswith("/" + manifest_name) for f in file_tree[:50]):
            try:
                # Find exact path
                target_path = manifest_name
                if manifest_name not in file_tree:
                    target_path = next(f for f in file_tree if f.endswith("/" + manifest_name))
                m_res = session.get(f"{base_api}/contents/{target_path}", headers=headers, timeout=5)
                if m_res.status_code == 200:
                    raw_b64 = m_res.json().get("content", "")
                    if raw_b64:
                        manifest_contents[manifest_name] = base64.b64decode(raw_b64).decode("utf-8", errors="replace")[:2500]
            except Exception:
                pass

    result["manifest_contents"] = manifest_contents

    # 5. Fetch Recent Commits
    try:
        commits_res = session.get(f"{base_api}/commits?per_page=5", headers=headers, timeout=6)
        if commits_res.status_code == 200:
            commits_list = []
            for c in commits_res.json():
                commit_info = c.get("commit", {})
                author_info = commit_info.get("author", {})
                commits_list.append({
                    "message": (commit_info.get("message") or "").splitlines()[0][:100],
                    "author": author_info.get("name", "Unknown"),
                    "date": author_info.get("date")
                })
            result["recent_commits"] = commits_list
    except Exception:
        pass

    # 6. Fetch Public Contributors
    try:
        contrib_res = session.get(f"{base_api}/contributors?per_page=10", headers=headers, timeout=6)
        if contrib_res.status_code == 200 and isinstance(contrib_res.json(), list):
            result["contributors"] = [
                {"login": c.get("login"), "contributions": c.get("contributions", 0)}
                for c in contrib_res.json()[:10] if isinstance(c, dict)
            ]
    except Exception:
        pass

    result["success"] = True
    result["status"] = "retrieved"
    return result

def extract_skill_signals(repo_data: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Derives deterministic skill signals from REAL retrieved repository data.
    
    Rules:
      - .py files -> Python signal
      - requirements.txt / pyproject.toml -> Python project signal
      - FastAPI in requirements/imports -> FastAPI signal
      - package.json -> JavaScript / Node.js signal
      - react / react-dom in package.json -> React signal
      - express in package.json -> Express signal
      - .sql files / migrations -> SQL / database signal
      - Dockerfile / docker-compose.yml -> Docker signal
      - .ts / .tsx / tsconfig.json -> TypeScript signal
      - .html / .css -> Web / Frontend signal
      - Git / GitHub Actions -> CI/CD signal
      
    DO NOT mark a skill solely because Gemini guesses it.
    Store the concrete source of each signal.
    """
    signals: Dict[str, Dict[str, str]] = {}

    file_tree = repo_data.get("file_tree", [])
    languages = repo_data.get("languages", {})
    manifests = repo_data.get("manifest_contents", {})
    topics = repo_data.get("topics", [])
    readme_text = (repo_data.get("readme_full") or repo_data.get("readme_summary") or "").lower()

    # 1. Python & Python Framework Signals
    py_files = [f for f in file_tree if f.endswith(".py")]
    has_reqs = any(f.endswith("requirements.txt") for f in file_tree)
    has_pyproject = any(f.endswith("pyproject.toml") for f in file_tree)
    has_setup = any(f.endswith("setup.py") for f in file_tree)

    if py_files or has_reqs or has_pyproject or "Python" in languages:
        py_bytes = languages.get("Python", 0)
        source_desc = []
        if has_reqs: source_desc.append("requirements.txt")
        if has_pyproject: source_desc.append("pyproject.toml")
        if py_files: source_desc.append(f"{len(py_files)} Python (.py) file(s)")
        if py_bytes: source_desc.append(f"{py_bytes:,} bytes of Python detected by GitHub")
        signals["Python"] = {
            "skill": "Python",
            "source": f"Real repository files: {', '.join(source_desc)}",
            "confidence": "High"
        }

    # Inspect requirements.txt / pyproject content
    reqs_text = manifests.get("requirements.txt", "").lower()
    pyproject_text = manifests.get("pyproject.toml", "").lower()
    combined_py_reqs = f"{reqs_text}\n{pyproject_text}"

    if "fastapi" in combined_py_reqs or "fastapi" in topics or ("from fastapi" in readme_text or "import fastapi" in readme_text):
        signals["FastAPI"] = {
            "skill": "FastAPI",
            "source": "fastapi declared in requirements/project configuration or repository topics",
            "confidence": "High"
        }
    if "django" in combined_py_reqs or "django" in topics or any("manage.py" in f for f in file_tree):
        signals["Django"] = {
            "skill": "Django",
            "source": "django dependency or manage.py detected in repository structure",
            "confidence": "High"
        }
    if "flask" in combined_py_reqs or "flask" in topics:
        signals["Flask"] = {
            "skill": "Flask",
            "source": "flask dependency identified in repository requirements",
            "confidence": "High"
        }
    if "torch" in combined_py_reqs or "pytorch" in combined_py_reqs or "pytorch" in topics:
        signals["PyTorch"] = {
            "skill": "PyTorch",
            "source": "PyTorch dependency identified in Python requirements/configuration",
            "confidence": "High"
        }
    if "tensorflow" in combined_py_reqs or "tensorflow" in topics:
        signals["TensorFlow"] = {
            "skill": "TensorFlow",
            "source": "TensorFlow dependency identified in Python requirements/configuration",
            "confidence": "High"
        }
    if "scikit-learn" in combined_py_reqs or "sklearn" in combined_py_reqs:
        signals["Machine Learning"] = {
            "skill": "Machine Learning",
            "source": "scikit-learn dependency identified in Python requirements",
            "confidence": "High"
        }
    if "sqlalchemy" in combined_py_reqs:
        signals["SQLAlchemy"] = {
            "skill": "SQLAlchemy",
            "source": "SQLAlchemy ORM dependency identified in Python requirements",
            "confidence": "High"
        }

    # 2. JavaScript / Node.js Ecosystem Signals
    has_package_json = any(f.endswith("package.json") for f in file_tree)
    js_files = [f for f in file_tree if f.endswith(".js") or f.endswith(".mjs") or f.endswith(".jsx")]
    
    if has_package_json or js_files or "JavaScript" in languages:
        js_bytes = languages.get("JavaScript", 0)
        source_desc = []
        if has_package_json: source_desc.append("package.json")
        if js_files: source_desc.append(f"{len(js_files)} JavaScript (.js/.jsx) file(s)")
        if js_bytes: source_desc.append(f"{js_bytes:,} bytes of JavaScript detected")
        signals["JavaScript"] = {
            "skill": "JavaScript",
            "source": f"Real repository files: {', '.join(source_desc)}",
            "confidence": "High"
        }

    pkg_text = manifests.get("package.json", "").lower()
    
    # React
    has_jsx = any(f.endswith(".jsx") for f in file_tree)
    if "react" in pkg_text or "react" in topics or has_jsx or "react" in readme_text:
        signals["React"] = {
            "skill": "React",
            "source": "React dependency in package.json or .jsx component files detected",
            "confidence": "High"
        }

    # Express
    if "express" in pkg_text or "express" in topics:
        signals["Express"] = {
            "skill": "Express",
            "source": "express dependency declared in package.json",
            "confidence": "High"
        }

    # Next.js
    if "next" in pkg_text or any("next.config" in f for f in file_tree):
        signals["Next.js"] = {
            "skill": "Next.js",
            "source": "Next.js framework dependency or next.config file detected",
            "confidence": "High"
        }

    # Vue
    if "vue" in pkg_text or any(f.endswith(".vue") for f in file_tree):
        signals["Vue.js"] = {
            "skill": "Vue.js",
            "source": "Vue framework dependency or .vue components detected",
            "confidence": "High"
        }

    # 3. TypeScript Signals
    ts_files = [f for f in file_tree if f.endswith(".ts") or f.endswith(".tsx")]
    has_tsconfig = any("tsconfig" in f for f in file_tree)
    if ts_files or has_tsconfig or "TypeScript" in languages:
        ts_bytes = languages.get("TypeScript", 0)
        signals["TypeScript"] = {
            "skill": "TypeScript",
            "source": f"Found {len(ts_files)} TypeScript (.ts/.tsx) files and tsconfig configuration ({ts_bytes:,} bytes detected)",
            "confidence": "High"
        }

    # 4. Docker / Containerization Signals
    has_dockerfile = any(f.endswith("Dockerfile") or "docker-compose" in f for f in file_tree) or "Dockerfile" in manifests
    if has_dockerfile or "docker" in topics:
        docker_files = [f for f in file_tree if "docker" in f.lower()]
        signals["Docker"] = {
            "skill": "Docker",
            "source": f"Found Docker configuration files: {', '.join(docker_files[:3]) if docker_files else 'Dockerfile in root'}",
            "confidence": "High"
        }

    # 5. SQL & Database Signals
    sql_files = [f for f in file_tree if f.endswith(".sql")]
    has_alembic = any("alembic" in f for f in file_tree)
    has_migrations = any("migration" in f.lower() for f in file_tree)
    has_prisma = any("prisma" in f for f in file_tree)
    if sql_files or has_alembic or has_migrations or has_prisma or "sql" in topics:
        db_sources = []
        if sql_files: db_sources.append(f"{len(sql_files)} .sql schema/query file(s)")
        if has_alembic: db_sources.append("Alembic database migrations")
        if has_prisma: db_sources.append("Prisma schema")
        signals["SQL / Database"] = {
            "skill": "SQL / Database",
            "source": f"Real database artifacts detected: {', '.join(db_sources) if db_sources else 'database migration files'}",
            "confidence": "High"
        }

    # 6. CI/CD & DevOps Signals
    has_gh_actions = any(".github/workflows" in f for f in file_tree)
    if has_gh_actions:
        workflow_files = [f for f in file_tree if ".github/workflows" in f]
        signals["CI/CD"] = {
            "skill": "CI/CD",
            "source": f"GitHub Actions workflows detected ({len(workflow_files)} workflow configuration files)",
            "confidence": "High"
        }

    # 7. Additional Languages
    other_langs = ["Go", "Java", "C++", "C", "Rust", "Ruby", "PHP", "HTML", "CSS"]
    for lang in other_langs:
        if lang in languages and languages[lang] > 500:
            signals[lang] = {
                "skill": lang,
                "source": f"GitHub detected {languages[lang]:,} bytes of {lang} source code",
                "confidence": "High"
            }

    return list(signals.values())

def build_repository_intelligence_summary(repo_data: Dict[str, Any], signals: List[Dict[str, str]]) -> str:
    """
    Converts GitHub API responses and extracted signals into a structured evidence summary.
    Enforces the IMPORTANT EVIDENCE RULE:
      - ProofHire may say: 'The repository contains evidence consistent with X development.'
      - ProofHire does NOT say: 'The candidate definitely developed this.'
      - Contributor information is shown as factual public repository metadata without inferring identity.
    """
    owner = repo_data.get("owner", "unknown")
    repo = repo_data.get("repo", "unknown")
    name = repo_data.get("repository_name", repo)
    desc = repo_data.get("description") or "No description provided."
    url = repo_data.get("repository_url") or f"https://github.com/{owner}/{repo}"
    primary_lang = repo_data.get("primary_language") or "Not detected"
    
    # Format languages
    langs = repo_data.get("languages", {})
    total_bytes = sum(langs.values()) if langs else 0
    if total_bytes > 0:
        lang_strs = [f"{k} ({round((v / total_bytes) * 100, 1)}%)" for k, v in sorted(langs.items(), key=lambda x: x[1], reverse=True)[:5]]
        lang_dist = ", ".join(lang_strs)
    else:
        lang_dist = primary_lang

    # Detected structure
    structure = repo_data.get("repository_structure", [])
    structure_str = ", ".join(structure[:10]) if structure else "Root-level files only"

    # Topics
    topics = repo_data.get("topics", [])
    topics_str = ", ".join(topics) if topics else "None"

    # README summary
    readme_summary = repo_data.get("readme_summary") or "README unavailable"

    # Recent activity
    commits = repo_data.get("recent_commits", [])
    if commits:
        recent_activity_str = f"Available ({len(commits)} recent commits recorded; latest commit '{commits[0].get('message', '')}' on {commits[0].get('date', 'recent')})"
    else:
        recent_activity_str = "Available" if not repo_data.get("is_empty") else "Empty repository"

    # Contributors
    contributors = repo_data.get("contributors", [])
    if contributors:
        contrib_names = [f"{c.get('login', 'unknown')} ({c.get('contributions', 0)} commits)" for c in contributors[:5]]
        contrib_str = f"{len(contributors)} public contributor(s) listed on GitHub: " + ", ".join(contrib_names)
    else:
        contrib_str = "Public contributor information not available or single contributor"

    # Signals
    if signals:
        signal_lines = [f"- {s.get('skill')}: {s.get('source')} [Confidence: {s.get('confidence', 'High')}]" for s in signals]
        signals_formatted = "\n".join(signal_lines)
        skill_names = ", ".join([s.get("skill") for s in signals[:6]])
        evidence_rule_note = f"The repository contains evidence consistent with {skill_names} development."
    else:
        signals_formatted = "- No specific skill frameworks detected from inspected files"
        evidence_rule_note = "The repository was retrieved, but no specific framework skill signals were detected."

    summary = f"""REPOSITORY INTELLIGENCE REPORT
==============================
Repository: {name} ({owner}/{repo})
Description: {desc}
URL: {url}
Primary Language: {primary_lang}
Language Distribution: {lang_dist}
Detected Structure: {structure_str}
Topics: {topics_str}

README Summary:
{readme_summary}

Recent Repository Activity: {recent_activity_str}
Public Contributors: {contrib_str}

Detected Skill Signals (Derived from real retrieved repository files):
{signals_formatted}

PROOFHIRE EVIDENCE INTEGRITY NOTE:
{evidence_rule_note}
(Note: GitHub repository existence does not prove that the candidate personally wrote every part of the repository. Contributor metadata reflects factual public GitHub records without inferring personal identity beyond available data.)
"""
    return summary.strip()
