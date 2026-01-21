from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Iterable

import requests

from .config import GitHubConfig


def _github_headers(token: str | None) -> dict:
    headers = {
        "Accept": "application/vnd.github.v3.raw",
        "User-Agent": "cv-builder",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def download_readme(repo_full_name: str, output_dir: Path, github: GitHubConfig) -> Path:
    owner, repo = repo_full_name.split("/", 1)
    url = f"{github.api_base}/repos/{owner}/{repo}/readme"
    response = requests.get(url, headers=_github_headers(github.token), timeout=30)
    if response.status_code == 404:
        raise ValueError(f"README not found for {repo_full_name}")
    if not response.ok:
        raise ValueError(f"Failed to fetch README for {repo_full_name}: {response.status_code} {response.text}")

    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"{owner}__{repo}__README.md"

    if response.headers.get("content-type", "").startswith("application/json"):
        payload = response.json()
        content = payload.get("content", "")
        decoded = base64.b64decode(content).decode("utf-8", errors="ignore")
        file_path.write_text(decoded, encoding="utf-8")
    else:
        file_path.write_text(response.text, encoding="utf-8")

    return file_path


def download_readmes(repo_list: Iterable[str], output_dir: Path, github: GitHubConfig) -> list[Path]:
    results = []
    for repo in repo_list:
        repo = repo.strip()
        if not repo:
            continue
        results.append(download_readme(repo, output_dir, github))
    return results


def load_readme_files(paths: Iterable[str]) -> dict[str, str]:
    readmes: dict[str, str] = {}
    for path in paths:
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"README file not found: {path}")
        readmes[file_path.name] = file_path.read_text(encoding="utf-8", errors="ignore")
    return readmes


def load_readme_directory(directory: str) -> dict[str, str]:
    base_dir = Path(directory)
    if not base_dir.exists():
        raise FileNotFoundError(f"README directory not found: {directory}")
    files = [str(p) for p in base_dir.glob("*.md")]
    return load_readme_files(files)
