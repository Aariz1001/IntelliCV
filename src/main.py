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
from .config_parser import load_config_from_file, create_default_config, ConfigParseError
from .docx_analyzer import DocxAnalyzer
from .content_optimizer import ContentOptimizer
from .change_tracker import ChangeReport
from .intelligent_builder import IntelligentCVBuilder
from .review_system import ReviewSystem
from .impact_translator import RealWorldImpactTranslator


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
    build_parser.add_argument("--config", help="Path to CV config file (markdown with YAML front matter)")
    build_parser.add_argument("--output-docx", required=True, help="Output DOCX path")
    build_parser.add_argument("--output-json", help="Optional output JSON path")

    interactive_parser = subparsers.add_parser("interactive", help="Interactively select repos and build CV")
    interactive_parser.add_argument("--cv", required=True, help="Path to input CV JSON")
    interactive_parser.add_argument("--repos", required=True, help="Path to text file with owner/repo per line")
    interactive_parser.add_argument(
        "--guidance",
        help="Optional tailoring guidance (you will be prompted if omitted)",
    )
    interactive_parser.add_argument("--config", help="Path to CV config file (markdown with YAML front matter)")
    interactive_parser.add_argument("--output-docx", required=True, help="Output DOCX path")
    interactive_parser.add_argument("--output-json", help="Optional output JSON path")
    interactive_parser.add_argument("--cache-dir", default=".readme_cache", help="Directory to cache downloaded READMEs")

    fetch_parser = subparsers.add_parser("fetch-readmes", help="Download README files from GitHub")
    fetch_parser.add_argument("--repos", required=True, help="Path to text file with owner/repo per line")
    fetch_parser.add_argument("--out", required=True, help="Output directory for README files")

    # CV Judge - ensemble AI analysis
    judge_parser = subparsers.add_parser("judge", help="Analyze CV against job description using AI ensemble")
    judge_parser.add_argument("--cv", required=True, help="Path or URL to CV (.txt, .md)")
    judge_parser.add_argument("--jd", required=True, help="Path or URL to job description")
    judge_parser.add_argument("--guidance", help="Optional evaluation guidance")

    # CV to JSON converter
    cv2json_parser = subparsers.add_parser("cv-to-json", help="Convert CV and job posting to structured JSON")
    cv2json_parser.add_argument("--cv", required=True, help="Path or URL to CV (.txt, .md)")
    cv2json_parser.add_argument("--jd", help="Optional path or URL to job description")
    cv2json_parser.add_argument("--output", help="Output JSON file path (default: prints to console)")

    # Job scraper
    scrape_parser = subparsers.add_parser("scrape-job", help="Scrape job posting from URL and save as markdown")
    scrape_parser.add_argument("url", help="URL of the job posting")
    scrape_parser.add_argument("--output", "-o", help="Output markdown file (default: job_posting.md)", default="job_posting.md")

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


def _handle_build(args: argparse.Namespace) -> None:
    """Build CV with optional config-driven optimization and interactive review."""
    config = load_config()
    
    cv_json = load_json(args.cv)
    validate_input_cv(cv_json)
    
    # Load CV config if provided
    cv_config = None
    if args.config:
        try:
            cv_config = load_config_from_file(args.config)
            print(f"[OK] Config loaded: {args.config}")
        except ConfigParseError as e:
            print(f"[X] Config error: {e}")
            return
    
    # Analyze DOCX if available and config provided
    current_pages = None
    if cv_config:
        try:
            # Try to get an existing DOCX to analyze current state
            docx_path = args.output_docx.replace(".docx", "_original.docx")
            if Path(docx_path).exists():
                analyzer = DocxAnalyzer(docx_path)
                current_pages = analyzer.estimate_page_count()
                print(f"[OK] Document analysis: Currently ~{current_pages} page(s)")
        except Exception as e:
            print(f"[!] Could not analyze existing DOCX (that's okay): {e}")
    
    # Apply intelligent optimization if config is provided
    optimized_cv = cv_json
    change_report = None
    if cv_config:
        try:
            print("\n[OPTIMIZE] Applying config-driven optimization...")
            builder = IntelligentCVBuilder(cv_json, cv_config, changes_dir="changes")
            optimized_cv, change_report = builder.optimize_for_page_limit(
                current_pages=current_pages,
                interactive=False
            )
            
            if change_report and change_report.changes:
                print(f"\n[CHANGES] Changes made:")
                print(f"   • Modifications: {len(change_report.changes)}")
                print(f"   • Words saved: {change_report.summary.get('total_words_saved', 0)}")
                
                # Show change summary
                review_system = ReviewSystem(changes_dir="changes")
                review_system.display_changes_summary(change_report)
                
                # Interactive approval
                print("\n" + "="*70)
                approval = input("Do you approve these changes? (y/n/d for details): ").strip().lower()
                
                if approval == 'd':
                    review_system.display_detailed_changes(change_report)
                    approval = input("Approve changes? (y/n): ").strip().lower()
                
                if approval != 'y':
                    print("[X] Changes rejected. Using original CV.")
                    optimized_cv = cv_json
                    change_report = None
                else:
                    print("[OK] Changes approved!")
                    review_system.save_change_report(change_report)
        except Exception as e:
            print(f"[!] Optimization error: {e}")
            print("  Proceeding with original CV")
            optimized_cv = cv_json
    
    # Load READMEs
    readmes = _load_readmes(args)
    
    # Tailor CV with AI using optimized content
    print("\n[AI] Tailoring CV with AI...")
    tailored = tailor_cv(optimized_cv, readmes, config.openrouter, guidance=args.guidance)
    validate_output_cv(tailored)
    
    # Save outputs
    if args.output_json:
        save_json(tailored, args.output_json)
        print(f"[OK] Saved tailored JSON to {args.output_json}")
    
    # Build DOCX with config format specs
    docx_format = cv_config.docx_format if cv_config else None
    build_docx(tailored, args.output_docx, docx_format=docx_format)
    print(f"[OK] Generated CV: {args.output_docx}")
    
    # Summary
    if change_report and change_report.changes:
        print(f"\n[STATS] Optimization Summary:")
        print(f"   • Final page limit: {cv_config.page_limit} page(s)")
        print(f"   • Total optimizations: {len(change_report.changes)}")
        print(f"   • Words removed: {change_report.summary.get('total_words_saved', 0)}")
        print(f"   • Reports saved to: changes/")



def _handle_interactive(args: argparse.Namespace) -> None:
    """Interactive mode with config-driven optimization and user review."""
    config = load_config()
    
    cv_json = load_json(args.cv)
    validate_input_cv(cv_json)
    
    # Load CV config if provided
    cv_config = None
    if args.config:
        try:
            cv_config = load_config_from_file(args.config)
            print(f"[OK] Config loaded: {args.config}")
        except ConfigParseError as e:
            print(f"[X] Config error: {e}")
            return
    
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
                print(f"  [OK] {repo}")
            except Exception as e:
                print(f"  ✗ {repo}: {e}")
    
    # Get guidance
    guidance = args.guidance
    if guidance is None:
        guidance = input("Optional tailoring guidance (press Enter to skip): ").strip() or None
    if guidance:
        print(f"Using guidance: {guidance}")
    
    # Apply intelligent optimization if config is provided
    optimized_cv = cv_json
    change_report = None
    if cv_config:
        try:
            print("\n[OPTIMIZE] Applying config-driven optimization...")
            builder = IntelligentCVBuilder(cv_json, cv_config, changes_dir="changes")
            optimized_cv, change_report = builder.optimize_for_page_limit(
                current_pages=None,
                interactive=False
            )
            
            if change_report and change_report.changes:
                print(f"\n[OK] Optimization complete: {len(change_report.changes)} changes")
                print(f"   Words saved: {change_report.summary.get('total_words_saved', 0)}")
                
                # Show summary
                review_system = ReviewSystem(changes_dir="changes")
                review_system.display_changes_summary(change_report)
                
                # Ask for approval
                print("\n" + "="*70)
                approval = input("Approve these optimizations? (y/n/d for details): ").strip().lower()
                
                if approval == 'd':
                    review_system.display_detailed_changes(change_report)
                    approval = input("Approve changes? (y/n): ").strip().lower()
                
                if approval != 'y':
                    print("[X] Optimizations rejected. Using original CV.")
                    optimized_cv = cv_json
                    change_report = None
                else:
                    print("[OK] Optimizations approved!")
                    review_system.save_change_report(change_report)
        except Exception as e:
            print(f"[!] Optimization error: {e}")
            print("  Proceeding with original CV")
            optimized_cv = cv_json
    
    print("\n[AI] Tailoring CV with AI...")
    tailored = tailor_cv(optimized_cv, readmes, config.openrouter, guidance=guidance)
    validate_output_cv(tailored)
    
    if args.output_json:
        save_json(tailored, args.output_json)
        print(f"[OK] Saved tailored JSON to {args.output_json}")
    
    # Build DOCX with config format specs
    docx_format = cv_config.docx_format if cv_config else None
    build_docx(tailored, args.output_docx, docx_format=docx_format)
    print(f"[OK] Generated CV: {args.output_docx}")
    
    # Summary
    if change_report and change_report.changes:
        print(f"\n[STATS] Build Summary:")
        print(f"   • Optimizations applied: {len(change_report.changes)}")
        print(f"   • Page limit: {cv_config.page_limit}")
        print(f"   • Reports: changes/")



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
    elif args.command == "judge":
        from .cv_judge import main_judge
        main_judge(args.cv, args.jd, args.guidance)
    elif args.command == "cv-to-json":
        from .cv_to_json import main_cv_to_json
        main_cv_to_json(args.cv, args.jd, args.output)
    elif args.command == "scrape-job":
        from .job_scraper import JobScraper
        scraper = JobScraper()
        try:
            scraper.scrape_and_save(args.url, args.output)
        except Exception as e:
            print(f"[X] Error: {e}")
            return


if __name__ == "__main__":
    main()
