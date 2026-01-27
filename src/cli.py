"""Modern CLI using Typer for CV Builder workflow management."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Optional, List
import json
import asyncio

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
from rich.prompt import Prompt, Confirm

from .config import load_config
from .config_parser import load_config_from_file, create_default_config, ConfigParseError
from .utils import load_json, save_json
from .cv_schema import validate_input_cv, validate_output_cv
from .docx_builder import build_docx
from .docx_analyzer import DocxAnalyzer
from .docx_metrics import DocxMetricsExtractor
from .content_optimizer import ContentOptimizer
from .intelligent_builder import IntelligentCVBuilder
from .review_system import ReviewSystem
from .tailoring import tailor_cv
from .github_readmes import download_readme, load_readme_directory, load_readme_files, download_readmes
from .change_tracker import ChangeReport

from script_files.docx_to_json import convert_docx_to_json as convert_docx_structural
from script_files.docx_to_text import extract_text_from_docx 

console = Console()
app = typer.Typer(
    name="cv-builder",
    help="AI-powered CV builder with GitHub integration, page optimization, and hiring-manager focused content",
    rich_markup_mode="rich"
)

# ============================================================================
# WORKFLOW STATE MANAGEMENT
# ============================================================================

class WorkflowStage(str, Enum):
    """CV building workflow stages."""
    CONVERT = "convert"
    FETCH_READMES = "fetch_readmes"
    SELECT_REPOS = "select_repos"
    OPTIMIZE = "optimize"
    TAILOR = "tailor"
    BUILD_DOCX = "build_docx"


class WorkflowState:
    """Track workflow progress."""
    
    def __init__(self, state_file: Path = Path(".cv_workflow_state")):
        self.state_file = state_file
        self.state = self._load_state()
    
    def _load_state(self) -> dict:
        """Load workflow state from file."""
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except Exception:
                return {}
        return {}
    
    def save_state(self):
        """Save workflow state to file."""
        self.state_file.write_text(json.dumps(self.state, indent=2, default=str))
    
    def mark_complete(self, stage: WorkflowStage, data: Optional[dict] = None):
        """Mark a stage as complete."""
        self.state[f"{stage.value}_complete"] = True
        if data:
            self.state[f"{stage.value}_data"] = data
        self.save_state()
        console.print(f"[green][OK][/green] Marked {stage.value} as complete")
    
    def is_complete(self, stage: WorkflowStage) -> bool:
        """Check if stage is complete."""
        return self.state.get(f"{stage.value}_complete", False)
    
    def get_data(self, stage: WorkflowStage) -> Optional[dict]:
        """Get saved data from stage."""
        return self.state.get(f"{stage.value}_data")
    
    def reset(self):
        """Reset workflow state."""
        self.state = {}
        self.save_state()
        console.print("[yellow]Workflow state reset[/yellow]")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _print_stage_header(title: str, description: str = ""):
    """Print a formatted stage header."""
    console.print(f"\n[bold blue]{'='*70}[/bold blue]")
    console.print(f"[bold cyan]{title}[/bold cyan]")
    if description:
        console.print(f"[dim]{description}[/dim]")
    console.print(f"[bold blue]{'='*70}[/bold blue]\n")


def _print_success(message: str):
    """Print success message."""
    console.print(f"[green][OK][/green] {message}")


def _print_error(message: str):
    """Print error message."""
    console.print(f"[red][ERROR][/red] {message}")


def _print_warning(message: str):
    """Print warning message."""
    console.print(f"[yellow][WARN][/yellow] {message}")


def _print_info(message: str):
    """Print info message."""
    console.print(f"[cyan][INFO][/cyan] {message}")


def _show_repo_selection_menu(repos: List[str]) -> List[str]:
    """Show interactive repo selection menu."""
    console.print("\n[bold]Available GitHub Repositories:[/bold]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("No.", style="cyan")
    table.add_column("Repository", style="green")
    
    for i, repo in enumerate(repos, 1):
        table.add_column(str(i), repo)
    
    console.print(table)
    
    console.print("[dim]Enter numbers separated by commas (e.g., 1,3,5)")
    console.print("Or type 'all' to select all, 'none' to skip[/dim]\n")
    
    selection = Prompt.ask("Your selection")
    
    if selection.lower() == "all":
        return repos
    elif selection.lower() == "none" or selection == "":
        return []
    
    try:
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
        
        return [repos[i] for i in indices if 0 <= i < len(repos)]
    except (ValueError, IndexError):
        _print_error("Invalid selection format")
        return []


# ============================================================================
# STAGE 1: CONVERT DOCX TO JSON
# ============================================================================

@app.command(name="convert")
def convert_docx_to_json_cmd(
    cv_file: Path = typer.Argument(
        ...,
        help="Path to CV file (.docx, .txt, .md, .markdown)",
        exists=True
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Output JSON path (default: cv_converted.json)"
    ),
    jd_file: Optional[Path] = typer.Option(
        None,
        "--job-description", "-jd",
        help="Optional job description to include",
        exists=True
    ),
    extract_metrics: bool = typer.Option(
        True,
        "--metrics/--no-metrics",
        help="Extract metrics from DOCX if available"
    ),
):
    """Convert CV document to structured JSON format.
    
    Uses structural parsing (not AI) for DOCX files via the docx_to_json.py script.
    This extracts real CV structure directly from the document.
    """
    _print_stage_header("CONVERT CV TO JSON", "Parse document and structure data")
    
    if output is None:
        output = Path("cv_converted.json")
    
    try:
        _print_info(f"Reading CV from: {cv_file}")
        
        is_docx = cv_file.suffix.lower() == ".docx"
        is_text = cv_file.suffix.lower() in [".txt", ".md", ".markdown"]
        
        cv_json = {}
        
        # For DOCX: Use structural parser (no AI)
        if is_docx:
            if convert_docx_structural is None:
                _print_error("Could not import docx_to_json parser. Using fallback text extraction.")
                # Fallback to text extraction
                text_content = extract_text_from_docx(str(cv_file))
                cv_json = {"raw_text": text_content}
            else:
                _print_info("Parsing DOCX structure (direct parsing, no AI)...")
                cv_json = convert_docx_structural(str(cv_file))
                _print_success("CV structure extracted")
        
        # For text files: Use the async AI converter as fallback
        elif is_text:
            _print_info(f"Converting {cv_file.suffix} using content parser...")
            from .cv_to_json import convert_cv_to_json
            cv_json = asyncio.run(convert_cv_to_json(str(cv_file)))
        
        else:
            _print_error(f"Unsupported file type: {cv_file.suffix}")
            return
        
        # Extract metrics from DOCX if available
        if is_docx and extract_metrics:
            try:
                _print_info("Extracting document metrics (fonts, margins, word count)...")
                metrics_extractor = DocxMetricsExtractor(cv_file)
                metrics = metrics_extractor.extract_all_metrics()
                cv_json["metrics"] = metrics
                _print_success(f"Extracted metrics: {metrics['word_count']} words, ~{metrics['page_count']} pages")
                if metrics.get('extracted_fonts', {}).get('family'):
                    _print_info(f"Detected font: {metrics['extracted_fonts']['family']}")
                    font_sizes = metrics['extracted_fonts'].get('detected_sizes', {})
                    if font_sizes:
                        sizes_str = ", ".join([f"{size}pt" for size in sorted(font_sizes.keys())])
                        _print_info(f"Font sizes detected: {sizes_str}")
            except Exception as e:
                _print_warning(f"Could not extract metrics: {e}")
        
        if jd_file:
            _print_info(f"Reading job description from: {jd_file}")
            jd_content = jd_file.read_text(encoding="utf-8")
            cv_json["job_description"] = jd_content
        
        save_json(cv_json, str(output))
        _print_success(f"Converted CV saved to: {output}")
        
        console.print(f"\n[cyan]CV Structure:[/cyan]")
        for key in cv_json.keys():
            if key not in ["job_description", "metrics"]:
                console.print(f"  • {key}")
        
        if "metrics" in cv_json:
            console.print(f"\n[cyan]Extracted Metrics:[/cyan]")
            metrics = cv_json["metrics"]
            console.print(f"  • Word count: {metrics.get('word_count', '?')}")
            console.print(f"  • Pages: ~{metrics.get('page_count', '?')}")
            console.print(f"  • Font: {metrics.get('extracted_fonts', {}).get('family', '?')}")
            if metrics.get('extracted_fonts', {}).get('detected_sizes'):
                console.print(f"  • Detected font sizes: {metrics['extracted_fonts']['detected_sizes']}")
    
    except Exception as e:
        _print_error(f"Conversion failed: {e}")
        raise typer.Exit(code=1)


# ============================================================================
# STAGE 2: FETCH GITHUB READMES
# ============================================================================

@app.command(name="fetch")
def fetch_readmes(
    repos_file: Path = typer.Argument(
        ...,
        help="Path to repos.txt file (owner/repo per line)",
        exists=True
    ),
    output_dir: Path = typer.Option(
        Path(".readme_cache"),
        "--output", "-o",
        help="Output directory for README files"
    ),
    token: Optional[str] = typer.Option(
        None,
        "--token",
        help="GitHub token (or use GITHUB_TOKEN env var)"
    ),
):
    """Download README files from GitHub repositories."""
    _print_stage_header("FETCH GITHUB READMES", "Download repository documentation")
    
    try:
        config = load_config()
        
        repos = [
            line.strip()
            for line in repos_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        
        if not repos:
            _print_warning("No repositories found in repos file")
            return
        
        _print_info(f"Found {len(repos)} repositories")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        success_count = 0
        for repo in track(repos, description="Downloading READMEs..."):
            try:
                download_readme(repo, output_dir, config.github)
                success_count += 1
            except Exception as e:
                _print_warning(f"Failed to fetch {repo}: {e}")
        
        _print_success(f"Downloaded {success_count}/{len(repos)} READMEs to {output_dir}")
    
    except Exception as e:
        _print_error(f"Fetch failed: {e}")
        raise typer.Exit(code=1)


# ============================================================================
# STAGE 3: OPTIMIZE CV CONTENT
# ============================================================================

@app.command(name="optimize")
def optimize_cv(
    cv_file: Path = typer.Argument(
        ...,
        help="Path to CV JSON file",
        exists=True
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config", "-c",
        help="Path to CV config file",
        exists=True
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        help="Require approval for changes"
    ),
):
    """Apply intelligent optimization to fit page limits."""
    _print_stage_header("OPTIMIZE CV CONTENT", "Reduce content to fit page limit")
    
    try:
        cv_json = load_json(str(cv_file))
        validate_input_cv(cv_json)
        
        if config_file is None:
            config_file = Path("my_config.md")
            if not config_file.exists():
                _print_warning(f"Config file not found, using defaults")
                cv_config = create_default_config()
            else:
                cv_config = load_config_from_file(str(config_file))
        else:
            cv_config = load_config_from_file(str(config_file))
        
        _print_info(f"Page limit: {cv_config.page_limit} page(s)")
        
        builder = IntelligentCVBuilder(cv_json, cv_config, changes_dir="changes")
        optimized_cv, change_report = builder.optimize_for_page_limit(interactive=interactive)
        
        if change_report and change_report.changes:
            console.print(f"\n[cyan]Changes Summary:[/cyan]")
            for change in change_report.changes[:5]:
                console.print(f"  • {change.change_type.value}: {change.reason}")
            
            if len(change_report.changes) > 5:
                console.print(f"  ... and {len(change_report.changes) - 5} more changes")
            
            _print_success(f"Optimization complete: {len(change_report.changes)} changes")
        else:
            _print_info("No changes needed - CV already optimal")
        
        return optimized_cv
    
    except ConfigParseError as e:
        _print_error(f"Config error: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        _print_error(f"Optimization failed: {e}")
        raise typer.Exit(code=1)


# ============================================================================
# STAGE 3B: OPTIMIZE + AI TAILOR (MERGED)
# ============================================================================

@app.command(name="enhance")
def enhance_cv(
    cv_file: Path = typer.Argument(
        ...,
        help="Path to CV JSON file",
        exists=True
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config", "-c",
        help="Path to CV config file",
        exists=True
    ),
    readme_dir: Optional[Path] = typer.Option(
        None,
        "--readme-dir",
        help="Directory with GitHub README files",
        exists=True
    ),
    skip_readme_selection: bool = typer.Option(
        False,
        "--skip-selection",
        help="Use all READMEs without selection prompt"
    ),
    guidance: Optional[str] = typer.Option(
        None,
        "--guidance", "-g",
        help="Custom tailoring guidance for AI"
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Output JSON path (default: cv_enhanced.json)"
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive/--no-interactive",
        help="Interactive review of changes"
    ),
):
    """Enhance CV with intelligent optimization AND AI tailoring (best of both worlds!)"""
    _print_stage_header("ENHANCE CV", "Optimize page fit + AI tailor for hiring managers")
    
    try:
        cv_json = load_json(str(cv_file))
        validate_input_cv(cv_json)
        
        if config_file is None:
            config_file = Path("my_config.md")
            if not config_file.exists():
                _print_warning(f"Config file not found, using defaults")
                cv_config = create_default_config()
            else:
                cv_config = load_config_from_file(str(config_file))
        else:
            cv_config = load_config_from_file(str(config_file))
        
        _print_info(f"Page limit: {cv_config.page_limit} page(s)")
        
        # Load READMEs if provided
        readmes = {}
        if readme_dir:
            _print_info(f"Loading READMEs from: {readme_dir}")
            all_readmes = load_readme_directory(str(readme_dir))
            
            if not skip_readme_selection and all_readmes:
                # Show selection menu interactively
                console.print("\n[bold]Available READMEs:[/bold]")
                readme_files = list(all_readmes.keys())
                
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("No.", style="cyan")
                table.add_column("Repository")
                
                for i, filename in enumerate(readme_files, 1):
                    table.add_row(str(i), filename)
                
                console.print(table)
                console.print("[dim]Enter numbers separated by commas (e.g., 1,3,5) or type 'all'/'none'[/dim]")
                
                selection = Prompt.ask("Your selection", default="all")
                
                if selection.lower() == "all":
                    readmes = all_readmes
                elif selection.lower() == "none" or selection == "":
                    readmes = {}
                else:
                    try:
                        indices = []
                        for part in selection.split(","):
                            part = part.strip()
                            if part.isdigit():
                                indices.append(int(part) - 1)
                        
                        readmes = {readme_files[i]: all_readmes[readme_files[i]] 
                                  for i in indices if i < len(readme_files)}
                        if not readmes:
                            _print_warning("Invalid selection, using all READMEs")
                            readmes = all_readmes
                    except (ValueError, IndexError) as e:
                        _print_warning(f"Selection error: {e}, using all READMEs")
                        readmes = all_readmes
            else:
                readmes = all_readmes
            
            _print_success(f"Using {len(readmes)} README file(s)")
        
        # Create builder and enhance
        builder = IntelligentCVBuilder(cv_json, cv_config, changes_dir="changes")
        
        # Show spinner while processing
        from rich.spinner import Spinner
        spinner = Spinner("dots", text="Processing CV...")
        try:
            with console.status(spinner, spinner_style="cyan"):
                enhanced_cv, change_report = builder.optimize_and_tailor(
                    readmes=readmes,
                    guidance=guidance,
                    interactive=interactive
                )
        except Exception as e:
            _print_error(f"Processing error: {e}")
            raise
        
        # Validate and save
        try:
            validate_output_cv(enhanced_cv)
        except Exception as e:
            _print_warning(f"Validation warning: {e}")
            _print_info("Attempting to fix validation issues...")
            
            # Restore all critical fields from original
            critical_fields = {
                "name": cv_json.get("name", "Unknown"),
                "title": cv_json.get("title", "Professional"),
                "contact": cv_json.get("contact", {}),
                "summary": cv_json.get("summary", []),
                "experience": cv_json.get("experience", []),
                "education": cv_json.get("education", []),
            }
            
            for field, original_value in critical_fields.items():
                if field not in enhanced_cv or not enhanced_cv.get(field):
                    enhanced_cv[field] = original_value
            
            # Try validation again
            try:
                validate_output_cv(enhanced_cv)
                _print_success("Validation issues fixed")
            except Exception as e2:
                _print_warning(f"Could not fully resolve validation: {e2}")
                # Continue anyway - better to have output than fail
        
        if output is None:
            output = Path("cv_enhanced.json")
        
        save_json(enhanced_cv, str(output))
        _print_success(f"Enhanced CV saved to: {output}")
        
        if change_report and change_report.changes:
            console.print(f"\n[cyan]Enhancement Summary:[/cyan]")
            console.print(f"  • Total changes: {len(change_report.changes)}")
            for change in change_report.changes[:3]:
                console.print(f"    - {change.change_type.value}: {change.reason}")
        
    except ConfigParseError as e:
        _print_error(f"Config error: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        _print_error(f"Enhancement failed: {e}")
        import traceback
        traceback.print_exc()
        raise typer.Exit(code=1)


# ============================================================================
# STAGE 4: TAILOR CV WITH AI
# ============================================================================

@app.command(name="tailor")
def tailor_cv_command(
    cv_file: Path = typer.Argument(
        ...,
        help="Path to CV JSON file",
        exists=True
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Output JSON path (default: cv_tailored.json)"
    ),
    readme_dir: Optional[Path] = typer.Option(
        None,
        "--readme-dir",
        help="Directory with README files",
        exists=True
    ),
    guidance: Optional[str] = typer.Option(
        None,
        "--guidance", "-g",
        help="Tailoring guidance for AI"
    ),
):
    """Tailor CV with AI using GitHub context and hiring-manager focus."""
    _print_stage_header("TAILOR CV WITH AI", "Apply 8-second hook strategy and GitHub context")
    
    try:
        config = load_config()
        cv_json = load_json(str(cv_file))
        validate_input_cv(cv_json)
        
        readmes = {}
        if readme_dir:
            _print_info(f"Loading READMEs from: {readme_dir}")
            readmes = load_readme_directory(str(readme_dir))
            _print_success(f"Loaded {len(readmes)} README files")
        
        if guidance is None:
            guidance = Prompt.ask("Optional tailoring guidance", default="")
            guidance = guidance or None
        
        _print_info("Sending to AI for tailoring...")
        _print_info("(This may take 30-120 seconds depending on CV complexity and API response time)")
        
        # Show progress while waiting
        from rich.spinner import Spinner
        spinner = Spinner("dots", text="AI is processing your CV...")
        with console.status(spinner, spinner_style="cyan"):
            tailored = tailor_cv(cv_json, readmes, config.openrouter, guidance=guidance)
        
        validate_output_cv(tailored)
        _print_success("AI tailoring complete")
        
        if output is None:
            output = Path("cv_tailored.json")
        
        save_json(tailored, str(output))
        _print_success(f"Tailored CV saved to: {output}")
    
    except Exception as e:
        _print_error(f"Tailoring failed: {e}")
        raise typer.Exit(code=1)


# ============================================================================
# STAGE 5: BUILD DOCX
# ============================================================================

@app.command(name="build")
def build_docx_command(
    cv_file: Path = typer.Argument(
        ...,
        help="Path to CV JSON file",
        exists=True
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Output DOCX path (default: cv_output.docx)"
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config", "-c",
        help="Path to CV config file",
        exists=True
    ),
):
    """Generate professional DOCX from CV JSON."""
    _print_stage_header("BUILD DOCX", "Generate formatted Word document")
    
    try:
        cv_json = load_json(str(cv_file))
        validate_output_cv(cv_json)
        
        if output is None:
            output = Path("cv_output.docx")
        
        docx_format = None
        if config_file is None:
            config_file = Path("my_config.md")
            if config_file.exists():
                cv_config = load_config_from_file(str(config_file))
                docx_format = cv_config.docx_format
        else:
            cv_config = load_config_from_file(str(config_file))
            docx_format = cv_config.docx_format
        
        _print_info(f"Building DOCX with {docx_format.page_size if docx_format else 'default'} format...")
        build_docx(cv_json, str(output), docx_format=docx_format)
        _print_success(f"CV document generated: {output}")
        
        # Validate output
        if output.exists():
            size_mb = output.stat().st_size / (1024 * 1024)
            _print_info(f"File size: {size_mb:.2f} MB")
    
    except Exception as e:
        _print_error(f"DOCX generation failed: {e}")
        raise typer.Exit(code=1)


# ============================================================================
# COMPLETE WORKFLOWS
# ============================================================================

@app.command(name="quick")
def quick_build(
    cv_file: Path = typer.Argument(
        ...,
        help="Path to CV JSON file",
        exists=True
    ),
    output_docx: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Output DOCX path"
    ),
    output_json: Optional[Path] = typer.Option(
        None,
        "--json",
        help="Also save optimized JSON"
    ),
    config_file: Optional[Path] = typer.Option(
        Path("my_config.md"),
        "--config", "-c",
        help="CV config file",
        exists=True
    ),
    readme_dir: Optional[Path] = typer.Option(
        Path(".readme_cache"),
        "--readme-dir",
        help="Directory with README files"
    ),
):
    """Quick full workflow: optimize → tailor → build DOCX."""
    _print_stage_header(
        "QUICK BUILD WORKFLOW",
        "Complete: Optimize → Tailor with AI → Build DOCX"
    )
    
    try:
        # Step 1: Optimize
        console.print("\n[bold magenta]Step 1/3: Optimizing CV content...[/bold magenta]")
        cv_config = load_config_from_file(str(config_file))
        cv_json = load_json(str(cv_file))
        validate_input_cv(cv_json)
        
        builder = IntelligentCVBuilder(cv_json, cv_config, changes_dir="changes")
        optimized_cv, _ = builder.optimize_for_page_limit(interactive=False)
        _print_success("CV content optimized")
        
        # Step 2: Tailor with AI
        console.print("\n[bold magenta]Step 2/3: Tailoring with AI...[/bold magenta]")
        config = load_config()
        readmes = {}
        
        if readme_dir and readme_dir.exists():
            readmes = load_readme_directory(str(readme_dir))
            _print_info(f"Using {len(readmes)} GitHub READMEs")
        
        tailored = tailor_cv(optimized_cv, readmes, config.openrouter)
        validate_output_cv(tailored)
        _print_success("CV tailored with AI")
        
        # Step 3: Build DOCX
        console.print("\n[bold magenta]Step 3/3: Building DOCX...[/bold magenta]")
        if output_docx is None:
            output_docx = Path("cv_final.docx")
        
        build_docx(tailored, str(output_docx), docx_format=cv_config.docx_format)
        _print_success(f"DOCX generated: {output_docx}")
        
        if output_json:
            save_json(tailored, str(output_json))
            _print_success(f"JSON saved: {output_json}")
        
        # Summary
        console.print(Panel(
            f"[green][OK] Build Complete![/green]\n"
            f"Output: {output_docx}\n"
            f"Format: {cv_config.docx_format.page_size}, "
            f"{cv_config.docx_format.margin_inches}\" margins\n"
            f"Pages: {cv_config.page_limit}",
            title="Build Summary",
            border_style="green"
        ))
    
    except Exception as e:
        _print_error(f"Build failed: {e}")
        raise typer.Exit(code=1)


@app.command(name="full")
def full_workflow(
    cv_file: Path = typer.Argument(
        ...,
        help="Path to CV JSON file",
        exists=True
    ),
    repos_file: Optional[Path] = typer.Option(
        Path("repos.txt"),
        "--repos",
        help="Path to repos.txt file",
        exists=True
    ),
    output_docx: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Output DOCX path"
    ),
    output_json: Optional[Path] = typer.Option(
        None,
        "--json",
        help="Also save optimized JSON"
    ),
    config_file: Optional[Path] = typer.Option(
        Path("my_config.md"),
        "--config", "-c",
        help="CV config file",
        exists=True
    ),
    interactive_repos: bool = typer.Option(
        True,
        "--interactive-repos/--all-repos",
        help="Interactively select repos or use all"
    ),
    guidance: Optional[str] = typer.Option(
        None,
        "--guidance", "-g",
        help="Tailoring guidance"
    ),
):
    """Full workflow: fetch READMEs → select repos → optimize → tailor → build."""
    _print_stage_header(
        "FULL WORKFLOW",
        "Complete: Fetch READMEs → Select Repos → Optimize → Tailor → Build"
    )
    
    try:
        config = load_config()
        cv_json = load_json(str(cv_file))
        validate_input_cv(cv_json)
        
        # Step 1: Fetch READMEs
        console.print("\n[bold magenta]Step 1/5: Fetching READMEs...[/bold magenta]")
        readme_dir = Path(".readme_cache")
        readme_dir.mkdir(exist_ok=True)
        
        repos = [
            line.strip()
            for line in repos_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        
        success = 0
        for repo in track(repos, description="Downloading..."):
            try:
                download_readme(repo, readme_dir, config.github)
                success += 1
            except Exception:
                pass
        
        _print_success(f"Downloaded {success}/{len(repos)} READMEs")
        
        # Step 2: Select repos
        console.print("\n[bold magenta]Step 2/5: Selecting repositories...[/bold magenta]")
        if interactive_repos:
            selected_repos = _show_repo_selection_menu(repos)
        else:
            selected_repos = repos
        
        _print_info(f"Using {len(selected_repos)} repositories")
        
        # Step 3: Optimize
        console.print("\n[bold magenta]Step 3/5: Optimizing content...[/bold magenta]")
        cv_config = load_config_from_file(str(config_file))
        builder = IntelligentCVBuilder(cv_json, cv_config, changes_dir="changes")
        optimized_cv, _ = builder.optimize_for_page_limit(interactive=False)
        _print_success("CV optimized")
        
        # Step 4: Tailor
        console.print("\n[bold magenta]Step 4/5: Tailoring with AI...[/bold magenta]")
        readmes = load_readme_directory(str(readme_dir))
        if guidance is None:
            guidance = Prompt.ask("Tailoring guidance", default="")
            guidance = guidance or None
        
        tailored = tailor_cv(optimized_cv, readmes, config.openrouter, guidance=guidance)
        validate_output_cv(tailored)
        _print_success("CV tailored")
        
        # Step 5: Build
        console.print("\n[bold magenta]Step 5/5: Building DOCX...[/bold magenta]")
        if output_docx is None:
            output_docx = Path("cv_final.docx")
        
        build_docx(tailored, str(output_docx), docx_format=cv_config.docx_format)
        _print_success(f"DOCX generated: {output_docx}")
        
        if output_json:
            save_json(tailored, str(output_json))
            _print_success(f"JSON saved: {output_json}")
        
        # Summary
        console.print(Panel(
            f"[green][OK] Full Workflow Complete![/green]\n"
            f"Output: {output_docx}\n"
            f"Repos: {len(selected_repos)}\n"
            f"Format: {cv_config.docx_format.page_size}, "
            f"{cv_config.docx_format.margin_inches}\" margins",
            title="Build Summary",
            border_style="green"
        ))
    
    except Exception as e:
        _print_error(f"Workflow failed: {e}")
        raise typer.Exit(code=1)


# ============================================================================
# UTILITY COMMANDS
# ============================================================================

@app.command(name="config")
def show_config(
    config_file: Optional[Path] = typer.Option(
        Path("my_config.md"),
        "--file", "-f",
        help="Path to config file",
        exists=True
    ),
):
    """Display current configuration."""
    _print_stage_header("CONFIGURATION", "Current CV builder settings")
    
    try:
        cv_config = load_config_from_file(str(config_file))
        
        # Page settings
        console.print("[bold cyan][DOC] Page Settings[/bold cyan]")
        table = Table(show_header=False)
        table.add_row("Page Size:", cv_config.docx_format.page_size)
        table.add_row("Page Limit:", f"{cv_config.page_limit} page(s)")
        table.add_row("Margins:", f"{cv_config.docx_format.margin_inches}\" all around")
        table.add_row("Available Height:", f"{cv_config.docx_format.constraints.available_height_inches}\"")
        console.print(table)
        
        # Font settings
        console.print("\n[bold cyan]🔤 Font Settings[/bold cyan]")
        table = Table(show_header=False)
        table.add_row("Font Family:", cv_config.docx_format.font_family)
        table.add_row("Name Size:", f"{cv_config.docx_format.font_sizes.name}pt")
        table.add_row("Section Heading:", f"{cv_config.docx_format.font_sizes.section_heading}pt")
        table.add_row("Body Text:", f"{cv_config.docx_format.font_sizes.bullet}pt")
        console.print(table)
        
        # Content constraints
        console.print("\n[bold cyan]📝 Content Constraints[/bold cyan]")
        table = Table(show_header=False)
        table.add_row("Words per Page:", str(cv_config.docx_format.constraints.words_per_page_estimate))
        table.add_row("Max Bullets/Role:", str(cv_config.docx_format.constraints.max_bullets_per_role))
        table.add_row("Max Projects:", str(cv_config.docx_format.constraints.max_projects))
        console.print(table)
        
        # Writing style
        console.print("\n[bold cyan][*] Writing Style[/bold cyan]")
        table = Table(show_header=False)
        table.add_row("Tone:", cv_config.style_preference.tone.value)
        table.add_row("Detail Level:", cv_config.style_preference.detail_level.value)
        table.add_row("Emphasis:", cv_config.style_preference.emphasis.value)
        console.print(table)
    
    except Exception as e:
        _print_error(f"Config load failed: {e}")
        raise typer.Exit(code=1)


@app.command(name="validate")
def validate_files(
    cv_file: Optional[Path] = typer.Argument(
        None,
        help="CV JSON file to validate"
    ),
    jd_file: Optional[Path] = typer.Option(
        None,
        "--jd",
        help="Job description to validate"
    ),
):
    """Validate CV and job description files."""
    _print_stage_header("VALIDATION", "Check file integrity and format")
    
    try:
        if cv_file and cv_file.exists():
            cv_json = load_json(str(cv_file))
            try:
                validate_input_cv(cv_json)
                _print_success(f"CV valid: {cv_file}")
            except Exception as e:
                _print_error(f"CV invalid: {e}")
                raise
        
        if jd_file and jd_file.exists():
            jd_content = jd_file.read_text()
            if jd_content.strip():
                _print_success(f"Job description valid: {jd_file}")
            else:
                _print_error("Job description is empty")
    
    except Exception as e:
        _print_error(f"Validation failed: {e}")
        raise typer.Exit(code=1)


@app.command(name="status")
def check_status():
    """Check workflow progress."""
    _print_stage_header("WORKFLOW STATUS", "Current progress and completion")
    
    state = WorkflowState()
    
    stages = [
        WorkflowStage.CONVERT,
        WorkflowStage.FETCH_READMES,
        WorkflowStage.SELECT_REPOS,
        WorkflowStage.OPTIMIZE,
        WorkflowStage.TAILOR,
        WorkflowStage.BUILD_DOCX,
    ]
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Stage", style="cyan")
    table.add_column("Status", style="green")
    
    completed = 0
    for stage in stages:
        status = "[OK] Complete" if state.is_complete(stage) else "○ Pending"
        table.add_row(stage.value.replace("_", " ").title(), status)
        if state.is_complete(stage):
            completed += 1
    
    console.print(table)
    console.print(f"\nProgress: {completed}/{len(stages)} stages complete")
    
    if completed == len(stages):
        console.print("[green][OK] Workflow complete![/green]")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    app()
