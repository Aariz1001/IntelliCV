from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    # dotenv not installed, will use os.environ directly
    pass


@dataclass(frozen=True)
class OpenRouterConfig:
    api_key: str
    model: str
    base_url: str = "https://openrouter.ai/api/v1"
    http_referer: str | None = None
    x_title: str | None = None


@dataclass(frozen=True)
class GitHubConfig:
    token: str | None = None
    api_base: str = "https://api.github.com"


@dataclass(frozen=True)
class AppConfig:
    openrouter: OpenRouterConfig
    github: GitHubConfig


def load_config() -> AppConfig:
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise ValueError("Missing OPENROUTER_API_KEY environment variable.")

    model = os.environ.get("OPENROUTER_MODEL", "google/gemini-3-flash-preview").strip()
    http_referer = os.environ.get("OPENROUTER_HTTP_REFERER")
    x_title = os.environ.get("OPENROUTER_X_TITLE")

    github_token = os.environ.get("GITHUB_TOKEN")

    openrouter = OpenRouterConfig(
        api_key=api_key,
        model=model,
        http_referer=http_referer,
        x_title=x_title,
    )
    github = GitHubConfig(token=github_token)
    return AppConfig(openrouter=openrouter, github=github)
