"""Main CV Judge entry point - ensemble AI CV analysis."""

from __future__ import annotations

import asyncio
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.markdown import Markdown

from .consensus_aggregator import ConsensusAggregator
from .content_ingestor import ContentIngestor
from .judge_models import AnalysisContext
from .judge_orchestrator import JudgeOrchestrator


console = Console()


def format_report(report) -> None:
    """Format and display the final report using Rich.
    
    Args:
        report: FinalReport object to display
    """
    console.print()
    
    # Header with consensus score
    score_color = "red" if report.consensus_score < 50 else "yellow" if report.consensus_score < 70 else "green"
    header = f"[bold {score_color}]Consensus Score: {report.consensus_score}/100[/bold {score_color}]"
    
    if report.judge_discordance:
        header += " [bold yellow][!]  DISCORDANCE DETECTED[/bold yellow]"
    
    console.print(Panel(header, title="[bold]CV Judge Ensemble Report[/bold]", border_style="blue"))
    
    # Recommendation
    console.print()
    console.print(Markdown(f"## {report.recommendation}"))
    console.print()
    
    # Consensus highlights
    if report.consensus_highlights:
        console.print("[bold cyan][*] Consensus Highlights:[/bold cyan]")
        for highlight in report.consensus_highlights:
            console.print(f"  • {highlight}")
        console.print()
    
    # Discordance points
    if report.discordance_points:
        console.print("[bold yellow][!]  Points of Disagreement:[/bold yellow]")
        for point in report.discordance_points:
            console.print(f"  • {point}")
        console.print()
    
    # Detailed breakdown table
    console.print("[bold]Individual Judge Evaluations:[/bold]")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Judge", style="cyan", width=20)
    table.add_column("Score", justify="center", width=8)
    table.add_column("Key Insights", width=60)
    
    for model_key, evaluation in report.detailed_breakdown.items():
        score_color = "red" if evaluation.score < 50 else "yellow" if evaluation.score < 70 else "green"
        
        # Compile insights
        insights = []
        if evaluation.matching_skills:
            insights.append(f"[OK] Skills: {', '.join(evaluation.matching_skills[:3])}")
            if len(evaluation.matching_skills) > 3:
                insights.append(f"  + {len(evaluation.matching_skills) - 3} more")
        
        if evaluation.missing_requirements:
            insights.append(f"✗ Missing: {', '.join(evaluation.missing_requirements[:2])}")
            if len(evaluation.missing_requirements) > 2:
                insights.append(f"  + {len(evaluation.missing_requirements) - 2} more")
        
        if evaluation.red_flags:
            insights.append(f"[!] Concerns: {', '.join(evaluation.red_flags[:2])}")
        
        insights_text = "\n".join(insights) if insights else "No specific insights"
        
        table.add_row(
            evaluation.model_name,
            f"[{score_color}]{evaluation.score}[/{score_color}]",
            insights_text
        )
    
    console.print(table)
    console.print()
    
    # Detailed rationales
    console.print("[bold]Detailed Rationales:[/bold]")
    for model_key, evaluation in report.detailed_breakdown.items():
        console.print(f"\n[cyan]{evaluation.model_name}:[/cyan]")
        console.print(f"  {evaluation.rationale}")
    
    console.print()


async def run_cv_judge(
    cv_source: str | Path,
    jd_source: str | Path,
    guidance: str | None = None,
    api_key: str | None = None
) -> None:
    """Run the CV judge ensemble analysis.
    
    Args:
        cv_source: Path or URL to the CV
        jd_source: Path or URL to the job description
        guidance: Optional guidance for the evaluation
        api_key: Optional OpenRouter API key
    """
    console.print("[bold blue]CV Judge - Ensemble AI Analysis[/bold blue]")
    console.print()
    
    # Step 1: Ingest content
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Loading CV and Job Description...", total=None)
        
        try:
            cv_text, cv_type = ContentIngestor.load_content(cv_source)
            cv_text = ContentIngestor.clean_text(cv_text)
            console.print(f"[OK] CV loaded from {cv_type}: {len(cv_text)} characters")
            
            jd_text, jd_type = ContentIngestor.load_content(jd_source)
            jd_text = ContentIngestor.clean_text(jd_text)
            console.print(f"[OK] Job Description loaded from {jd_type}: {len(jd_text)} characters")
            
        except Exception as e:
            console.print(f"[bold red]Error loading content:[/bold red] {e}")
            return
        
        progress.remove_task(task)
    
    console.print()
    
    # Step 2: Create analysis context
    context = AnalysisContext(
        cv_text=cv_text,
        jd_text=jd_text,
        guidance=guidance
    )
    
    # Step 3: Run ensemble evaluation
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(
            "Querying AI judges (Gemini 3, Kimi K2, GLM-4.7)...",
            total=None
        )
        
        try:
            async with JudgeOrchestrator(api_key=api_key) as orchestrator:
                evaluations = await orchestrator.run_ensemble(context)
            
            if not evaluations:
                console.print("[bold red]Error: All judges failed to respond[/bold red]")
                return
            
            console.print(f"[OK] Received {len(evaluations)}/3 judge evaluations")
            
        except Exception as e:
            console.print(f"[bold red]Error during evaluation:[/bold red] {e}")
            return
        
        progress.remove_task(task)
    
    console.print()
    
    # Step 4: Aggregate results
    report = ConsensusAggregator.aggregate(evaluations)
    
    # Step 5: Display report
    format_report(report)


def main_judge(
    cv: str,
    jd: str,
    guidance: str | None = None
) -> None:
    """Main entry point for the judge command.
    
    Args:
        cv: Path or URL to the CV
        jd: Path or URL to the job description
        guidance: Optional guidance for evaluation
    """
    asyncio.run(run_cv_judge(cv, jd, guidance))


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 3:
        console.print("[bold red]Usage:[/bold red] python -m src.cv_judge <cv_path_or_url> <jd_path_or_url> [guidance]")
        sys.exit(1)
    
    cv_arg = sys.argv[1]
    jd_arg = sys.argv[2]
    guidance_arg = sys.argv[3] if len(sys.argv) > 3 else None
    
    main_judge(cv_arg, jd_arg, guidance_arg)
