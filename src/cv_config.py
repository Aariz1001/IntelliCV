"""CV Configuration schema and utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Any
from enum import Enum


class PriorityLevel(str, Enum):
    """Priority levels for CV sections."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class TonePreference(str, Enum):
    """Tone preferences for CV writing style."""
    FORMAL = "formal"
    PROFESSIONAL = "professional"
    CASUAL = "casual"


class DetailLevel(str, Enum):
    """Detail level preferences."""
    CONCISE = "concise"
    BALANCED = "balanced"
    DETAILED = "detailed"


class EmphasisStyle(str, Enum):
    """What to emphasize in the CV."""
    IMPACT_METRICS = "impact_metrics"
    TECHNICAL_DEPTH = "technical_depth"
    GROWTH_TRAJECTORY = "growth_trajectory"
    BALANCED = "balanced"


@dataclass
class StylePreference:
    """User's style preferences for CV writing."""
    tone: TonePreference = TonePreference.PROFESSIONAL
    detail_level: DetailLevel = DetailLevel.CONCISE
    emphasis: EmphasisStyle = EmphasisStyle.IMPACT_METRICS

    def to_dict(self) -> dict[str, str]:
        return {
            "tone": self.tone.value,
            "detail_level": self.detail_level.value,
            "emphasis": self.emphasis.value,
        }


@dataclass
class SectionPriorities:
    """Priority levels for each CV section."""
    experience: PriorityLevel = PriorityLevel.HIGH
    projects: PriorityLevel = PriorityLevel.HIGH
    skills: PriorityLevel = PriorityLevel.MEDIUM
    education: PriorityLevel = PriorityLevel.MEDIUM
    certifications: PriorityLevel = PriorityLevel.LOW
    awards: PriorityLevel = PriorityLevel.LOW

    def to_dict(self) -> dict[str, str]:
        return {
            "experience": self.experience.value,
            "projects": self.projects.value,
            "skills": self.skills.value,
            "education": self.education.value,
            "certifications": self.certifications.value,
            "awards": self.awards.value,
        }

    def get_priority_value(self, section: str) -> int:
        """Get numeric priority value (higher = more important)."""
        priority_map = {
            PriorityLevel.HIGH: 3,
            PriorityLevel.MEDIUM: 2,
            PriorityLevel.LOW: 1,
        }
        section_priority = getattr(self, section.lower(), PriorityLevel.LOW)
        return priority_map.get(section_priority, 1)


@dataclass
class StructureConfig:
    """Structure and ordering of CV sections."""
    sections: list[str] = field(default_factory=lambda: [
        "experience", "projects", "skills", "education", "certifications"
    ])
    order: Optional[list[int]] = None  # Custom ordering if needed

    def get_section_order(self) -> list[str]:
        """Get sections in specified order."""
        if self.order is None:
            return self.sections
        return [self.sections[i] for i in self.order if i < len(self.sections)]


@dataclass
class ProjectPrioritizationWeights:
    """Weights for project prioritization factors."""
    technical_complexity: float = 0.3
    impact_metrics: float = 0.3
    maturity: float = 0.2
    keyword_relevance: float = 0.1
    recency: float = 0.1

    def normalize(self) -> ProjectPrioritizationWeights:
        """Normalize weights to sum to 1.0."""
        total = (
            self.technical_complexity +
            self.impact_metrics +
            self.maturity +
            self.keyword_relevance +
            self.recency
        )
        if total == 0:
            return self
        return ProjectPrioritizationWeights(
            technical_complexity=self.technical_complexity / total,
            impact_metrics=self.impact_metrics / total,
            maturity=self.maturity / total,
            keyword_relevance=self.keyword_relevance / total,
            recency=self.recency / total,
        )


@dataclass
class CVRules:
    """DOs and DONTs for CV generation."""
    dos: list[str] = field(default_factory=lambda: [
        "Use quantified metrics",
        "Include real-world impact",
        "Action-verb-first bullets",
        "Focus on outcomes over tasks",
    ])
    donts: list[str] = field(default_factory=lambda: [
        "Avoid buzzwords",
        "Don't list tools without context",
        "Don't use passive voice",
        "Don't exceed page limit",
    ])


@dataclass
class DocxFontSizes:
    """Font sizes for different DOCX elements."""
    name: int = 14
    title: int = 10
    section_heading: int = 10
    role_header: int = 9
    bullet: int = 9
    skills_label: int = 9
    contact_info: int = 8

    def to_dict(self) -> dict[str, int]:
        return {
            "name": self.name,
            "title": self.title,
            "section_heading": self.section_heading,
            "role_header": self.role_header,
            "bullet": self.bullet,
            "skills_label": self.skills_label,
            "contact_info": self.contact_info,
        }
    
    @classmethod
    def from_dict(cls, data: Optional[dict]) -> DocxFontSizes:
        """Create from dict, using defaults if None."""
        if data is None:
            return cls()
        return cls(
            name=data.get("name", 14),
            title=data.get("title", 10),
            section_heading=data.get("section_heading", 10),
            role_header=data.get("role_header", 9),
            bullet=data.get("bullet", 9),
            skills_label=data.get("skills_label", 9),
            contact_info=data.get("contact_info", 8),
        )


@dataclass
class DocxSpacing:
    """Spacing settings for DOCX elements (in points)."""
    section_before: int = 6
    section_after: int = 2
    role_before: int = 3
    role_after: int = 1
    bullet_before: int = 0
    bullet_after: int = 1
    name_before: int = 0
    name_after: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "section_before": self.section_before,
            "section_after": self.section_after,
            "role_before": self.role_before,
            "role_after": self.role_after,
            "bullet_before": self.bullet_before,
            "bullet_after": self.bullet_after,
            "name_before": self.name_before,
            "name_after": self.name_after,
        }


@dataclass
class DocxConstraints:
    """Physical and content constraints for DOCX formatting."""
    max_pages: int = 1
    available_height_inches: float = 10.94
    available_width_inches: float = 7.77
    words_per_page_estimate: int = 250
    max_bullets_per_role: int = 5
    max_projects: int = 3

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_pages": self.max_pages,
            "available_height_inches": self.available_height_inches,
            "available_width_inches": self.available_width_inches,
            "words_per_page_estimate": self.words_per_page_estimate,
            "max_bullets_per_role": self.max_bullets_per_role,
            "max_projects": self.max_projects,
        }
    
    @classmethod
    def from_dict(cls, data: Optional[dict]) -> DocxConstraints:
        """Create from dict, using defaults if None."""
        if data is None:
            return cls()
        return cls(
            max_pages=data.get("max_pages", 1),
            available_height_inches=data.get("available_height_inches", 10.94),
            available_width_inches=data.get("available_width_inches", 7.77),
            words_per_page_estimate=data.get("words_per_page_estimate", 250),
            max_bullets_per_role=data.get("max_bullets_per_role", 5),
            max_projects=data.get("max_projects", 3),
        )


@dataclass
class DocxFormatting:
    """Visual formatting for DOCX elements."""
    name_bold: bool = True
    section_headers_bold: bool = True
    section_headers_underlined: bool = True
    role_headers_bold: bool = True
    role_headers_italics: bool = False
    use_bullets: bool = True
    bullet_indent_inches: float = 0.25

    def to_dict(self) -> dict[str, Any]:
        return {
            "name_bold": self.name_bold,
            "section_headers_bold": self.section_headers_bold,
            "section_headers_underlined": self.section_headers_underlined,
            "role_headers_bold": self.role_headers_bold,
            "role_headers_italics": self.role_headers_italics,
            "use_bullets": self.use_bullets,
            "bullet_indent_inches": self.bullet_indent_inches,
        }


@dataclass
class DocxFormat:
    """Complete DOCX format specification."""
    page_size: str = "A4"
    page_width_inches: float = 8.27
    page_height_inches: float = 11.69
    margin_inches: float = 0.25
    font_family: str = "Lora"
    font_sizes: DocxFontSizes = field(default_factory=DocxFontSizes)
    spacing: DocxSpacing = field(default_factory=DocxSpacing)
    constraints: DocxConstraints = field(default_factory=DocxConstraints)
    formatting: DocxFormatting = field(default_factory=DocxFormatting)

    def to_dict(self) -> dict[str, Any]:
        return {
            "page_size": self.page_size,
            "page_width_inches": self.page_width_inches,
            "page_height_inches": self.page_height_inches,
            "margin_inches": self.margin_inches,
            "font_family": self.font_family,
            "font_sizes": self.font_sizes.to_dict(),
            "spacing": self.spacing.to_dict(),
            "constraints": self.constraints.to_dict(),
            "formatting": self.formatting.to_dict(),
        }



@dataclass
class CVConfig:
    """Complete CV configuration."""
    page_limit: int
    total_pages: int = 1
    style_preference: StylePreference = field(default_factory=StylePreference)
    docx_format: DocxFormat = field(default_factory=DocxFormat)
    priorities: SectionPriorities = field(default_factory=SectionPriorities)
    structure: StructureConfig = field(default_factory=StructureConfig)
    project_prioritization: ProjectPrioritizationWeights = field(
        default_factory=ProjectPrioritizationWeights
    )
    rules: CVRules = field(default_factory=CVRules)

    def validate(self) -> tuple[bool, list[str]]:
        """Validate config. Returns (is_valid, list_of_errors)."""
        errors = []

        if not isinstance(self.page_limit, int) or self.page_limit < 1 or self.page_limit > 3:
            errors.append("page_limit must be an integer between 1 and 3")

        if not isinstance(self.style_preference, StylePreference):
            errors.append("style_preference must be a StylePreference object")

        if not isinstance(self.priorities, SectionPriorities):
            errors.append("priorities must be a SectionPriorities object")

        if not isinstance(self.structure, StructureConfig):
            errors.append("structure must be a StructureConfig object")

        if len(self.structure.sections) == 0:
            errors.append("structure.sections must have at least one section")

        weights = self.project_prioritization.normalize()
        if abs(sum([weights.technical_complexity, weights.impact_metrics,
                    weights.maturity, weights.keyword_relevance, weights.recency]) - 1.0) > 0.01:
            errors.append("project_prioritization weights must sum to approximately 1.0")

        return len(errors) == 0, errors

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "page_limit": self.page_limit,
            "total_pages": self.total_pages,
            "style_preference": self.style_preference.to_dict(),
            "docx_format": self.docx_format.to_dict(),
            "priorities": self.priorities.to_dict(),
            "structure": {
                "sections": self.structure.sections,
                "order": self.structure.order,
            },
            "project_prioritization": {
                "technical_complexity": self.project_prioritization.technical_complexity,
                "impact_metrics": self.project_prioritization.impact_metrics,
                "maturity": self.project_prioritization.maturity,
                "keyword_relevance": self.project_prioritization.keyword_relevance,
                "recency": self.project_prioritization.recency,
            },
            "rules": {
                "dos": self.rules.dos,
                "donts": self.rules.donts,
            },
        }
