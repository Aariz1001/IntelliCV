"""Interactive user review system for CV optimization changes."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .change_tracker import ChangeReport


class ReviewSystem:
    """Interactive system for user to review and approve/steer CV changes."""

    def __init__(self, changes_dir: str | Path = "changes"):
        """Initialize review system.
        
        Args:
            changes_dir: Directory to save change reports
        """
        self.changes_dir = Path(changes_dir)
        self.changes_dir.mkdir(parents=True, exist_ok=True)

    def display_changes_summary(self, report: ChangeReport) -> None:
        """Display changes summary in terminal with formatting.
        
        Args:
            report: ChangeReport to display
        """
        summary = report.summary

        # Print header
        self._print_section("CV OPTIMIZATION SUMMARY")

        # Stats
        print(f"\n[CHANGES] Changes Made:")
        print(f"   • Total changes: {summary.get('total_changes', 0)}")
        print(f"   • Words removed: {summary.get('total_words_saved', 0)}")

        # By type
        by_type = summary.get("changes_by_type", {})
        if by_type:
            print(f"\n📋 Changes by Type:")
            for change_type, count in sorted(by_type.items()):
                emoji = self._get_emoji_for_type(change_type)
                print(f"   {emoji} {change_type.title()}: {count}")

        # By section
        by_section = summary.get("changes_by_section", {})
        if by_section:
            print(f"\n📑 Changes by Section:")
            for section, count in sorted(by_section.items()):
                print(f"   • {section.title()}: {count}")

    def display_detailed_changes(self, report: ChangeReport, max_changes: int = 10) -> None:
        """Display detailed changes grouped by section.
        
        Args:
            report: ChangeReport to display
            max_changes: Maximum number of changes to show
        """
        if not report.changes:
            print("\nNo detailed changes to display.")
            return

        print(f"\n{'='*70}")
        print(f"DETAILED CHANGES (showing first {min(len(report.changes), max_changes)})")
        print(f"{'='*70}\n")

        # Group by section
        by_section = {}
        for change in report.changes:
            if change.section not in by_section:
                by_section[change.section] = []
            by_section[change.section].append(change)

        count = 0
        for section in sorted(by_section.keys()):
            print(f"\n🏷️  {section.upper()}")
            print(f"{'-'*70}")

            for change in by_section[section]:
                if count >= max_changes:
                    print(f"\n... and {len(report.changes) - count} more changes")
                    return

                emoji = self._get_emoji_for_type(change.change_type.value)
                print(f"\n{emoji} [{change.change_type.value.upper()}] {change.item_key}")
                print(f"   💭 Reason: {change.reason}")
                print(f"   📝 Words saved: {change.words_saved}")

                # Show before/after if available
                if change.before_content:
                    before_preview = (change.before_content[:70] + "...") if len(change.before_content) > 70 else change.before_content
                    print(f"   Before: \"{before_preview}\"")

                if change.after_content and change.change_type.value != "removed":
                    after_preview = (change.after_content[:70] + "...") if len(change.after_content) > 70 else change.after_content
                    print(f"   After:  \"{after_preview}\"")

                count += 1

    def prompt_for_approval(self) -> str:
        """Prompt user to approve, reject, or steer changes.
        
        Returns:
            "approve", "reject", or "steer"
        """
        self._print_section("\nREVIEW REQUIRED")

        print("\nWhat would you like to do?")
        print("  [A] Approve changes and continue [OK]")
        print("  [R] Reject changes and revert [X]")
        print("  [S] Steer AI in different direction [->]")
        print("  [D] Show more detailed changes 📖")
        print("\nEnter your choice (A/R/S/D):")

        while True:
            choice = input("Your choice: ").strip().upper()
            if choice in ("A", "APPROVE"):
                return "approve"
            elif choice in ("R", "REJECT"):
                return "reject"
            elif choice in ("S", "STEER"):
                return "steer"
            elif choice in ("D", "DETAIL"):
                return "detail"
            else:
                print("Invalid choice. Please enter A, R, S, or D.")

    def prompt_for_steering_instructions(self) -> str:
        """Prompt user for steering instructions to guide AI.
        
        Returns:
            Steering instructions as string
        """
        self._print_section("\nSTEERING INSTRUCTIONS")

        print("\nProvide guidance to redirect the optimization:")
        print("Examples:")
        print("  - 'Keep all projects, trim experience instead'")
        print("  - 'Preserve education details, focus on condensing bullets'")
        print("  - 'Prioritize recent projects over older ones'")
        print("  - 'Emphasize impact metrics more than technical depth'")
        print("\nYour instructions (press Enter twice when done):")

        lines = []
        try:
            while True:
                line = input()
                if line.strip() == "":
                    if lines:
                        break
                else:
                    lines.append(line)
        except EOFError:
            pass

        return "\n".join(lines)

    def save_change_report(self, report: ChangeReport, prefix: str = "cv_optimization") -> None:
        """Save change report to files.
        
        Args:
            report: ChangeReport to save
            prefix: Prefix for filenames
        """
        report.calculate_summary()

        # Save JSON
        json_path = self.changes_dir / f"{prefix}_detailed.json"
        json_path.write_text(report.to_json(), encoding="utf-8")
        print(f"\n[OK] Saved detailed changes: {json_path}")

        # Save markdown summary
        md_path = self.changes_dir / f"{prefix}_summary.md"
        md_path.write_text(report.to_markdown_summary(), encoding="utf-8")
        print(f"[OK] Saved markdown summary: {md_path}")

        # Save text summary
        txt_path = self.changes_dir / f"{prefix}_summary.txt"
        txt_path.write_text(report.to_text_summary(), encoding="utf-8")
        print(f"[OK] Saved text summary: {txt_path}")

    @staticmethod
    def _print_section(title: str) -> None:
        """Print a formatted section header."""
        print(f"\n{'='*70}")
        print(f"{title.center(70)}")
        print(f"{'='*70}")

    @staticmethod
    def _get_emoji_for_type(change_type: str) -> str:
        """Get emoji for a change type."""
        emojis = {
            "removed": "🗑️",
            "condensed": "📉",
            "reordered": "[SYNC]",
            "modified": "✏️",
            "added": "➕",
        }
        return emojis.get(change_type.lower(), "•")


def create_changes_directory(output_dir: Optional[str | Path] = None) -> Path:
    """Create changes directory for storing reports.
    
    Args:
        output_dir: Optional base directory (defaults to project root)
        
    Returns:
        Path to changes directory
    """
    if output_dir:
        changes_dir = Path(output_dir) / "changes"
    else:
        changes_dir = Path("changes")

    changes_dir.mkdir(parents=True, exist_ok=True)
    return changes_dir
