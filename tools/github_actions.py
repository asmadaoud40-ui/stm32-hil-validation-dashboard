"""Read-only GitHub Actions status access for the local dashboard."""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class GitHubActionsError(RuntimeError):
    """Raised when GitHub Actions status cannot be retrieved."""


def _get_json(url: str, token: str | None = None, timeout: int = 10) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "STM32-HIL-Validation-Dashboard",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(url, headers=headers, method="GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        if error.code == 403:
            raise GitHubActionsError(
                "GitHub API refused the request (permissions or rate limit)."
            ) from error
        if error.code == 404:
            raise GitHubActionsError(
                "Repository or workflow not found, or access is not authorized."
            ) from error
        raise GitHubActionsError(f"GitHub API returned HTTP {error.code}.") from error
    except URLError as error:
        raise GitHubActionsError(f"Network connection to GitHub failed: {error.reason}") from error
    except TimeoutError as error:
        raise GitHubActionsError("GitHub API request timed out.") from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise GitHubActionsError("GitHub API returned an invalid response.") from error


def fetch_latest_workflow_run(
    repository: str,
    workflow_file: str,
    branch: str = "main",
    token: str | None = None,
) -> dict:
    """Return the newest workflow run and its job/step details.

    The endpoint is read-only. A token is optional for public repositories and,
    when used, should be supplied through the GITHUB_TOKEN environment variable.
    """
    repository = repository.strip().strip("/")
    workflow_file = workflow_file.strip().strip("/")
    branch = branch.strip()

    if repository.count("/") != 1 or not all(repository.split("/")):
        raise GitHubActionsError(
            "Invalid repository setting. Expected the form owner/repository."
        )
    if not workflow_file or not branch:
        raise GitHubActionsError("Workflow filename and branch must be configured.")

    encoded_workflow = quote(workflow_file, safe="")
    encoded_branch = quote(branch, safe="")
    base = f"https://api.github.com/repos/{repository}"
    runs_url = (
        f"{base}/actions/workflows/{encoded_workflow}/runs"
        f"?branch={encoded_branch}&per_page=1"
    )
    payload = _get_json(runs_url, token=token)
    runs = payload.get("workflow_runs", [])
    if not runs:
        return {"run": None, "jobs": [], "repository": repository}

    run = runs[0]
    run_id = run.get("id")
    if not run_id:
        raise GitHubActionsError("The latest workflow run has no run ID.")

    jobs_url = f"{base}/actions/runs/{run_id}/jobs?per_page=100"
    jobs_payload = _get_json(jobs_url, token=token)
    return {
        "run": run,
        "jobs": jobs_payload.get("jobs", []),
        "repository": repository,
    }
