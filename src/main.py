from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import load_dotenv

from .config import load_config
from .cv_schema import validate_input_cv, validate_output_cv
from .docx_builder import build_docx
from .github_readmes import download_readme, load_readme_directory, load_readme_files
from .tailoring import tailor_cv
from .utils import load_json, save_json


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI CV builder")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Tailor CV and generate DOCX")
    build_parser.add_argument("--cv", required=True, help="Path to input CV JSON")
    build_parser.add_argument("--readme-dir", help="Directory with README .md files")
    build_parser.add_argument("--readme", action="append", default=[], help="Path to a README file (repeatable)")
    build_parser.add_argument(
        "--guidance",
        help="Optional tailoring guidance (e.g., 'prioritize ML projects, keep wording close')",
    )
    build_parser.add_argument("--output-docx", required=True, help="Output DOCX path")
    build_parser.add_argument("--output-json", help="Optional output JSON path")

    interactive_parser = subparsers.add_parser("interactive", help="Interactively select repos and build CV")
    interactive_parser.add_argument("--cv", required=True, help="Path to input CV JSON")
    interactive_parser.add_argument("--repos", required=True, help="Path to text file with owner/repo per line")
    interactive_parser.add_argument(
        "--guidance",
        help="Optional tailoring guidance (you will be prompted if omitted)",
    )
    interactive_parser.add_argument("--output-docx", required=True, help="Output DOCX path")
    interactive_parser.add_argument("--output-json", help="Optional output JSON path")
    interactive_parser.add_argument("--cache-dir", default=".readme_cache", help="Directory to cache downloaded READMEs")

    fetch_parser = subparsers.add_parser("fetch-readmes", help="Download README files from GitHub")
    fetch_parser.add_argument("--repos", required=True, help="Path to text file with owner/repo per line")
    fetch_parser.add_argument("--out", required=True, help="Output directory for README files")

    return parser.parse_args()


def _load_readmes(args: argparse.Namespace) -> dict[str, str]:
    readmes: dict[str, str] = {}
    if args.readme_dir:
        readmes.update(load_readme_directory(args.readme_dir))
    if args.readme:
        readmes.update(load_readme_files(args.readme))
    return readmes


def _print_repo_menu(repos: list[str]) -> None:
    print("\n" + "=" * 50)
    print("Available GitHub Repositories:")
    print("=" * 50)
    for i, repo in enumerate(repos, 1):
        print(f"  [{i}] {repo}")
    print("=" * 50)
    print("Enter numbers separated by commas (e.g., 1,3,5)")
    print("Or type 'all' to select all, 'none' to skip")
    print("=" * 50)


def _parse_selection(selection: str, max_index: int) -> list[int]:
    selection = selection.strip().lower()
    if selection == "all":
        return list(range(max_index))
    if selection == "none" or selection == "":
        return []
    
    indices = []
    for part in selection.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            start_idx = int(start.strip()) - 1
            end_idx = int(end.strip()) - 1
            indices.extend(range(start_idx, end_idx + 1))
        else:
            indices.append(int(part) - 1)
    
    return [i for i in indices if 0 <= i < max_index]


def _handle_interactive(args: argparse.Namespace) -> None:
    config = load_config()

    cv_json = load_json(args.cv)
    validate_input_cv(cv_json)

    repo_list = [
        line.strip()
        for line in Path(args.repos).read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    if not repo_list:
        print("No repositories found in the repos file.")
        return

    _print_repo_menu(repo_list)
    selection = input("Your selection: ")
    selected_indices = _parse_selection(selection, len(repo_list))

    if not selected_indices:
        print("No repositories selected. Proceeding without README context.")
        readmes: dict[str, str] = {}
    else:
        selected_repos = [repo_list[i] for i in selected_indices]
        print(f"\nSelected {len(selected_repos)} repositories:")
        for repo in selected_repos:
            print(f"  - {repo}")

        cache_dir = Path(args.cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)

        readmes = {}
        for repo in selected_repos:
            print(f"Fetching README for {repo}...")
            try:
                readme_path = download_readme(repo, cache_dir, config.github)
                readmes[readme_path.name] = readme_path.read_text(encoding="utf-8", errors="ignore")
                print(f"  ✓ {repo}")
            except Exception as e:
                print(f"  ✗ {repo}: {e}")

    guidance = args.guidance
    if guidance is None:
        guidance = input("Optional tailoring guidance (press Enter to skip): ").strip() or None
    if guidance:
        print(f"Using guidance: {guidance}")

    print("\nTailoring CV with AI...")
    tailored = tailor_cv(cv_json, readmes, config.openrouter, guidance=guidance)
    validate_output_cv(tailored)

    if args.output_json:
        save_json(tailored, args.output_json)
        print(f"Saved tailored JSON to {args.output_json}")

    build_docx(tailored, args.output_docx)
    print(f"Generated CV: {args.output_docx}")


def _handle_build(args: argparse.Namespace) -> None:
    config = load_config()

    cv_json = load_json(args.cv)
    validate_input_cv(cv_json)

    readmes = _load_readmes(args)
    tailored = tailor_cv(cv_json, readmes, config.openrouter, guidance=args.guidance)
    validate_output_cv(tailored)

    if args.output_json:
        save_json(tailored, args.output_json)

    build_docx(tailored, args.output_docx)


def _handle_fetch_readmes(args: argparse.Namespace) -> None:
    config = load_config()
    repo_list = Path(args.repos).read_text(encoding="utf-8").splitlines()
    from .github_readmes import download_readmes
    download_readmes(repo_list, Path(args.out), config.github)


def main() -> None:
    load_dotenv()
    args = _parse_args()
    if args.command == "build":
        _handle_build(args)
    elif args.command == "interactive":
        _handle_interactive(args)
    elif args.command == "fetch-readmes":
        _handle_fetch_readmes(args)


if __name__ == "__main__":
    main()
