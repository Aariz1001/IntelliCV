"""Track and report changes made to CV during optimization."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Any


class ChangeType(str, Enum):
    """Types of changes that can be made to a CV."""
    REMOVED = "removed"
    CONDENSED = "condensed"
    REORDERED = "reordered"
    MODIFIED = "modified"
    ADDED = "added"


@dataclass
class Change:
    """A single change made to the CV."""
    change_type: ChangeType
    section: str
    item_key: str  # e.g., "experience_0", "project_1"
    before_content: str
    after_content: str
    reason: str
    words_saved: int = 0
    importance: str = "MEDIUM"  # LOW, MEDIUM, HIGH

    def to_dict(self) -> dict[str, Any]:
        return {
            "change_type": self.change_type.value,
            "section": self.section,
            "item_key": self.item_key,
            "before_content": self.before_content,
            "after_content": self.after_content,
            "reason": self.reason,
            "words_saved": self.words_saved,
            "importance": self.importance,
        }


@dataclass
class ChangeReport:
    """Complete report of all changes made to a CV."""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    changes: list[Change] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)

    def add_change(self, change: Change) -> None:
        """Add a change to the report."""
        self.changes.append(change)

    def calculate_summary(self) -> None:
        """Calculate summary statistics."""
        by_type = {}
        by_section = {}
        total_words_saved = 0

        for change in self.changes:
            # Count by type
            change_type = change.change_type.value
            by_type[change_type] = by_type.get(change_type, 0) + 1

            # Count by section
            section = change.section
            by_section[section] = by_section.get(section, 0) + 1

            # Sum words saved
            total_words_saved += change.words_saved

        self.summary = {
            "total_changes": len(self.changes),
            "changes_by_type": by_type,
            "changes_by_section": by_section,
            "total_words_saved": total_words_saved,
            "timestamp": self.timestamp,
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "timestamp": self.timestamp,
            "summary": self.summary,
            "changes": [change.to_dict() for change in self.changes],
        }

    def to_json(self) -> str:
        """Convert report to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    def to_markdown_summary(self) -> str:
        """Convert report to markdown format (human-readable summary)."""
        lines = []
        lines.append("# CV Optimization Changes\n")
        lines.append(f"**Generated**: {self.timestamp}\n")

        # Summary stats
        lines.append("## Summary\n")
        lines.append(f"- **Total Changes**: {self.summary.get('total_changes', 0)}")
        lines.append(f"- **Words Saved**: {self.summary.get('total_words_saved', 0)}")

        # By type
        by_type = self.summary.get("changes_by_type", {})
        if by_type:
            lines.append("\n### Changes by Type\n")
            for change_type, count in by_type.items():
                lines.append(f"- **{change_type.title()}**: {count}")

        # By section
        by_section = self.summary.get("changes_by_section", {})
        if by_section:
            lines.append("\n### Changes by Section\n")
            for section, count in by_section.items():
                lines.append(f"- **{section.title()}**: {count}")

        # Detailed changes
        if self.changes:
            lines.append("\n## Detailed Changes\n")

            # Group by section
            by_section_dict = {}
            for change in self.changes:
                if change.section not in by_section_dict:
                    by_section_dict[change.section] = []
                by_section_dict[change.section].append(change)

            for section in sorted(by_section_dict.keys()):
                lines.append(f"### {section.title()}\n")
                for change in by_section_dict[section]:
                    lines.append(f"\n**{change.change_type.value.upper()}** ({change.item_key})")
                    lines.append(f"- Reason: {change.reason}")
                    lines.append(f"- Words Saved: {change.words_saved}")

                    if change.before_content and change.before_content != change.after_content:
                        lines.append(f"- Before: `{change.before_content[:100]}...`")
                        if change.after_content:
                            lines.append(f"- After: `{change.after_content[:100]}...`")

        return "\n".join(lines)

    def to_text_summary(self) -> str:
        """Convert report to plain text format."""
        lines = []
        lines.append("=" * 70)
        lines.append("CV OPTIMIZATION CHANGES REPORT")
        lines.append("=" * 70)
        lines.append(f"\nGenerated: {self.timestamp}\n")

        # Summary stats
        lines.append("SUMMARY")
        lines.append("-" * 70)
        lines.append(f"Total Changes: {self.summary.get('total_changes', 0)}")
        lines.append(f"Words Saved: {self.summary.get('total_words_saved', 0)}\n")

        # By type
        by_type = self.summary.get("changes_by_type", {})
        if by_type:
            lines.append("CHANGES BY TYPE")
            lines.append("-" * 70)
            for change_type, count in sorted(by_type.items()):
                lines.append(f"  {change_type.title()}: {count}")
            lines.append("")

        # By section
        by_section = self.summary.get("changes_by_section", {})
        if by_section:
            lines.append("CHANGES BY SECTION")
            lines.append("-" * 70)
            for section, count in sorted(by_section.items()):
                lines.append(f"  {section.title()}: {count}")
            lines.append("")

        # Detailed changes
        if self.changes:
            lines.append("DETAILED CHANGES")
            lines.append("=" * 70)

            by_section_dict = {}
            for change in self.changes:
                if change.section not in by_section_dict:
                    by_section_dict[change.section] = []
                by_section_dict[change.section].append(change)

            for section in sorted(by_section_dict.keys()):
                lines.append(f"\n{section.upper()}")
                lines.append("-" * 70)
                for change in by_section_dict[section]:
                    lines.append(f"\n  [{change.change_type.value.upper()}] {change.item_key}")
                    lines.append(f"  Reason: {change.reason}")
                    lines.append(f"  Words Saved: {change.words_saved}")

                    if change.before_content and change.before_content != change.after_content:
                        before_preview = (change.before_content[:80] + "...")
                        after_preview = (change.after_content[:80] + "...") if change.after_content else "(removed)"
                        lines.append(f"  Before: {before_preview}")
                        lines.append(f"  After:  {after_preview}")

        lines.append("\n" + "=" * 70)
        return "\n".join(lines)
