"""Intelligent content optimization for CV tailoring."""

from __future__ import annotations

from typing import Any, Optional
from dataclasses import dataclass
from datetime import datetime

from .cv_config import CVConfig, PriorityLevel
from .change_tracker import ChangeReport, Change, ChangeType


@dataclass
class ProjectMetrics:
    """Metrics for a project used in prioritization."""
    name: str
    technical_complexity: float = 0.5  # 0-1 scale
    impact_metrics_present: bool = False
    maturity_score: float = 0.5  # 0-1: newer projects < 0.5, older > 0.5
    keyword_relevance_score: float = 0.5  # 0-1: how relevant to job
    recency_days: int = 365  # Days since project completion
    description: str = ""

    def calculate_priority_score(self, weights) -> float:
        """Calculate overall priority score using weights from config."""
        # Normalize recency (recent = high score)
        recency_score = max(0, 1 - (self.recency_days / 1825))  # 5 years = cutoff

        score = (
            weights.technical_complexity * self.technical_complexity +
            weights.impact_metrics * (1.0 if self.impact_metrics_present else 0.3) +
            weights.maturity * self.maturity_score +
            weights.keyword_relevance * self.keyword_relevance_score +
            weights.recency * recency_score
        )
        return score


class ContentOptimizer:
    """Optimize CV content to fit within page limits while maintaining quality."""

    def __init__(self, config: CVConfig):
        """Initialize optimizer with configuration.
        
        Args:
            config: CVConfig with optimization rules and priorities
        """
        self.config = config
        self.change_report = ChangeReport()

    def score_item_importance(self, section: str, item_index: int) -> float:
        """Score the importance of an item for removal decisions.
        
        Args:
            section: Section name (experience, projects, etc.)
            item_index: Index within section
            
        Returns:
            Importance score (higher = more important to keep)
        """
        # Base score from section priority
        section_priority = self.config.priorities.get_priority_value(section)
        base_score = section_priority * 10

        # Boost for items that are more recent (lower index = newer, so boost)
        position_boost = max(0, 5 - item_index)

        return base_score + position_boost

    def rank_projects_for_removal(
        self,
        projects: list[dict[str, Any]],
    ) -> list[tuple[int, float]]:
        """Rank projects by priority for removal (if needed).
        
        Args:
            projects: List of project dicts from CV
            
        Returns:
            List of (index, priority_score) tuples, sorted by removal priority (lowest first)
        """
        weights = self.config.project_prioritization.normalize()
        ranked = []

        for idx, project in enumerate(projects):
            metrics = self._extract_project_metrics(project, idx)
            score = metrics.calculate_priority_score(weights)
            ranked.append((idx, score))

        # Sort by score (ascending = remove lowest scoring first)
        ranked.sort(key=lambda x: x[1])
        return ranked

    def _extract_project_metrics(self, project: dict, index: int) -> ProjectMetrics:
        """Extract metrics from a project dict.
        
        Args:
            project: Project dict from CV JSON
            index: Position in projects list
            
        Returns:
            ProjectMetrics object
        """
        name = project.get("name", "Unnamed Project")
        description = " ".join(project.get("bullets", []))
        dates = project.get("dates", "")

        # Estimate technical complexity from keywords
        tech_keywords = {
            "machine learning", "ai", "llm", "deep learning", "neural",
            "kubernetes", "distributed", "microservices", "architecture",
            "optimization", "performance", "algorithm", "database", "sql"
        }
        description_lower = description.lower()
        tech_score = sum(1 for keyword in tech_keywords if keyword in description_lower) / len(tech_keywords)
        tech_score = min(1.0, tech_score * 0.5)  # Cap at 0.5 before boost
        tech_score += 0.3  # Base score

        # Check for impact metrics
        metric_keywords = {"increased", "decreased", "improved", "reduced", "%", "x faster", "times"}
        has_metrics = any(keyword in description_lower for keyword in metric_keywords)

        # Estimate maturity from dates (older = more mature)
        maturity = 0.5
        if dates:
            try:
                # Extract year (simplified)
                year_str = dates.split("-")[-1].strip()
                if year_str.isdigit():
                    current_year = datetime.now().year
                    year = int(year_str)
                    maturity = min(1.0, (current_year - year) / 5)
            except (ValueError, IndexError):
                pass

        # Keyword relevance (would need job description to score properly)
        keyword_score = 0.5

        # Recency
        recency_days = 365
        if dates:
            try:
                year_str = dates.split("-")[-1].strip()
                if year_str.isdigit():
                    current_year = datetime.now().year
                    year = int(year_str)
                    recency_days = (current_year - year) * 365
            except (ValueError, IndexError):
                pass

        return ProjectMetrics(
            name=name,
            technical_complexity=tech_score,
            impact_metrics_present=has_metrics,
            maturity_score=maturity,
            keyword_relevance_score=keyword_score,
            recency_days=recency_days,
            description=description[:200],
        )

    def get_section_items_removable(self, section: str, item_count: int) -> list[int]:
        """Get indices of items that CAN be removed (respecting minimum count).
        
        For each section, ensure at least 1 item remains.
        
        Args:
            section: Section name
            item_count: Total items in section
            
        Returns:
            List of indices that can be safely removed
        """
        if item_count <= 1:
            # Cannot remove - must keep at least one
            return []

        # Can remove all but the first (most important)
        return list(range(1, item_count))

    def remove_sections_by_priority(
        self,
        cv_json: dict[str, Any],
        words_to_remove: int,
    ) -> dict[str, Any]:
        """Remove items from sections based on priority.
        
        Args:
            cv_json: CV data
            words_to_remove: Target number of words to remove
            
        Returns:
            Modified CV JSON with items removed/condensed
        """
        remaining_words = words_to_remove
        modified_cv = self._deep_copy_cv(cv_json)

        # Get sections in priority order (lowest priority first)
        sections_by_priority = self._get_sections_in_removal_order()

        for section in sections_by_priority:
            if remaining_words <= 0:
                break

            items = modified_cv.get(section, [])
            if not isinstance(items, list) or len(items) == 0:
                continue

            # Get removable items (keeping at least 1)
            removable_indices = self.get_section_items_removable(section, len(items))

            # Remove items in reverse order to maintain indices
            for idx in reversed(removable_indices):
                if remaining_words <= 0:
                    break

                item = items[idx]
                item_text = self._extract_item_text(section, item)
                item_words = len(item_text.split())

                # Remove this item
                items.pop(idx)
                remaining_words -= item_words

                # Track change
                self.change_report.add_change(Change(
                    change_type=ChangeType.REMOVED,
                    section=section,
                    item_key=f"{section}_{idx}",
                    before_content=item_text[:100],
                    after_content="",
                    reason=f"Lower priority item removed to reduce content",
                    words_saved=item_words,
                    importance=self._get_item_importance(section, idx),
                ))

        return modified_cv

    def condense_bullets_in_section(
        self,
        cv_json: dict[str, Any],
        section: str,
        target_reduction: float = 0.2,  # 20% reduction
    ) -> dict[str, Any]:
        """Condense bullets in a specific section (remove redundancy, tighten wording).
        
        Args:
            cv_json: CV data
            section: Section to condense
            target_reduction: Target percentage of words to remove (0-1)
            
        Returns:
            Modified CV with condensed content
        """
        modified_cv = self._deep_copy_cv(cv_json)
        items = modified_cv.get(section, [])

        if not isinstance(items, list):
            return modified_cv

        for idx, item in enumerate(items):
            if not isinstance(item, dict) or "bullets" not in item:
                continue

            bullets = item.get("bullets", [])
            condensed_bullets = []

            for bullet in bullets:
                # Condense by removing common phrases, redundancy
                condensed = self._condense_bullet(bullet)
                words_removed = len(bullet.split()) - len(condensed.split())

                if len(condensed.split()) > 5:  # Keep non-empty bullets
                    condensed_bullets.append(condensed)

                    if words_removed > 0:
                        self.change_report.add_change(Change(
                            change_type=ChangeType.CONDENSED,
                            section=section,
                            item_key=f"{section}_{idx}_bullet",
                            before_content=bullet[:100],
                            after_content=condensed[:100],
                            reason="Removed redundancy and tightened wording",
                            words_saved=words_removed,
                            importance="MEDIUM",
                        ))

            item["bullets"] = condensed_bullets

        return modified_cv

    def _condense_bullet(self, bullet: str) -> str:
        """Condense a single bullet point.
        
        Args:
            bullet: Bullet text
            
        Returns:
            Condensed bullet text
        """
        # Remove common verbose phrases
        verbose_phrases = {
            "Responsible for": "",
            "In charge of": "",
            "Worked on": "",
            "Helped to": "",
            "Was able to": "",
            "is able to": "",
            "also": "",
            " and also ": ", ",
        }

        condensed = bullet
        for phrase, replacement in verbose_phrases.items():
            condensed = condensed.replace(phrase, replacement)

        # Remove extra spaces
        condensed = " ".join(condensed.split())

        return condensed

    def _extract_item_text(self, section: str, item: dict) -> str:
        """Extract readable text from a CV item."""
        text_parts = []

        # Name/title fields
        for key in ["name", "role", "company", "school", "title"]:
            if key in item and item[key]:
                text_parts.append(str(item[key]))

        # Bullets
        if "bullets" in item and isinstance(item["bullets"], list):
            text_parts.extend(item["bullets"])

        return " ".join(text_parts)

    def _get_sections_in_removal_order(self) -> list[str]:
        """Get sections in order of removal priority (lowest priority first)."""
        sections = [
            ("certifications", PriorityLevel.LOW),
            ("awards", PriorityLevel.LOW),
            ("education", PriorityLevel.MEDIUM),
            ("skills", PriorityLevel.MEDIUM),
            ("projects", PriorityLevel.HIGH),
            ("experience", PriorityLevel.HIGH),
        ]

        # Sort by priority (LOW first, HIGH last)
        priority_order = {PriorityLevel.LOW: 0, PriorityLevel.MEDIUM: 1, PriorityLevel.HIGH: 2}
        sections_sorted = sorted(
            sections,
            key=lambda x: priority_order.get(x[1], 1)
        )

        return [section for section, _ in sections_sorted]

    def _get_item_importance(self, section: str, index: int) -> str:
        """Get importance level for an item."""
        priority = self.config.priorities.get_priority_value(section)
        if priority >= 3:
            return "HIGH"
        elif priority >= 2:
            return "MEDIUM"
        else:
            return "LOW"

    def _deep_copy_cv(self, cv_json: dict[str, Any]) -> dict[str, Any]:
        """Create a deep copy of CV JSON."""
        import copy
        return copy.deepcopy(cv_json)

    def get_change_report(self) -> ChangeReport:
        """Get the change report with all modifications."""
        self.change_report.calculate_summary()
        return self.change_report
