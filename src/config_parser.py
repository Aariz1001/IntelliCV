"""Config file parser for CV configuration (Markdown with YAML front matter)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:
    yaml = None

from .cv_config import (
    CVConfig,
    StylePreference,
    SectionPriorities,
    StructureConfig,
    ProjectPrioritizationWeights,
    CVRules,
    TonePreference,
    DetailLevel,
    EmphasisStyle,
    PriorityLevel,
    DocxFormat,
    DocxFontSizes,
    DocxSpacing,
    DocxConstraints,
    DocxFormatting,
)


class ConfigParseError(Exception):
    """Raised when config file cannot be parsed."""
    pass


def _extract_yaml_front_matter(content: str) -> tuple[Optional[str], str]:
    """Extract YAML front matter from markdown content.
    
    Returns (yaml_content, markdown_content) where yaml_content is None if not found.
    """
    if not content.startswith("---"):
        return None, content

    # Find closing ---
    try:
        end_index = content.index("---", 3)  # Start searching after opening ---
    except ValueError:
        return None, content

    yaml_content = content[3:end_index].strip()
    markdown_content = content[end_index + 3:].strip()

    return yaml_content, markdown_content


def _parse_yaml_dict(yaml_content: str) -> dict[str, Any]:
    """Parse YAML string to dictionary."""
    if yaml is None:
        raise ConfigParseError("PyYAML is required to parse config files. Install with: pip install pyyaml")

    try:
        data = yaml.safe_load(yaml_content)
        return data if isinstance(data, dict) else {}
    except yaml.YAMLError as e:
        raise ConfigParseError(f"Failed to parse YAML front matter: {e}")


def _parse_style_preference(data: dict[str, Any]) -> StylePreference:
    """Parse style preference from config data."""
    style_data = data.get("style_preference", {})
    if not isinstance(style_data, dict):
        raise ConfigParseError("style_preference must be a dictionary")

    tone = style_data.get("tone", "professional")
    detail_level = style_data.get("detail_level", "concise")
    emphasis = style_data.get("emphasis", "impact_metrics")

    try:
        return StylePreference(
            tone=TonePreference(tone),
            detail_level=DetailLevel(detail_level),
            emphasis=EmphasisStyle(emphasis),
        )
    except ValueError as e:
        raise ConfigParseError(f"Invalid style preference value: {e}")


def _parse_priorities(data: dict[str, Any]) -> SectionPriorities:
    """Parse priorities from config data."""
    priorities_data = data.get("priorities", {})
    if not isinstance(priorities_data, dict):
        raise ConfigParseError("priorities must be a dictionary")

    kwargs = {}
    for section in ["experience", "projects", "skills", "education", "certifications", "awards"]:
        if section in priorities_data:
            try:
                kwargs[section] = PriorityLevel(priorities_data[section])
            except ValueError:
                raise ConfigParseError(
                    f"Invalid priority level for '{section}'. "
                    f"Must be one of: {', '.join(p.value for p in PriorityLevel)}"
                )

    return SectionPriorities(**kwargs)


def _parse_structure(data: dict[str, Any]) -> StructureConfig:
    """Parse structure from config data."""
    structure_data = data.get("structure", {})
    if not isinstance(structure_data, dict):
        raise ConfigParseError("structure must be a dictionary")

    sections = structure_data.get("sections")
    order = structure_data.get("order")

    if sections is None:
        return StructureConfig()

    if not isinstance(sections, list):
        raise ConfigParseError("structure.sections must be a list")

    if order is not None and not isinstance(order, list):
        raise ConfigParseError("structure.order must be a list of integers")

    return StructureConfig(sections=sections, order=order)


def _parse_project_prioritization(data: dict[str, Any]) -> ProjectPrioritizationWeights:
    """Parse project prioritization weights from config data."""
    weights_data = data.get("project_prioritization", {})
    if not isinstance(weights_data, dict):
        raise ConfigParseError("project_prioritization must be a dictionary")

    kwargs = {}
    weight_fields = [
        "technical_complexity",
        "impact_metrics",
        "maturity",
        "keyword_relevance",
        "recency",
    ]

    for field in weight_fields:
        if field in weights_data:
            try:
                kwargs[field] = float(weights_data[field])
            except (ValueError, TypeError):
                raise ConfigParseError(f"project_prioritization.{field} must be a number")

    return ProjectPrioritizationWeights(**kwargs)


def _parse_rules(data: dict[str, Any]) -> CVRules:
    """Parse rules (DOs and DONTs) from config data."""
    rules_data = data.get("rules", {})
    if not isinstance(rules_data, dict):
        raise ConfigParseError("rules must be a dictionary")

    dos = rules_data.get("dos", [])
    donts = rules_data.get("donts", [])

    if not isinstance(dos, list):
        raise ConfigParseError("rules.dos must be a list")
    if not isinstance(donts, list):
        raise ConfigParseError("rules.donts must be a list")

    return CVRules(dos=dos, donts=donts)


def _parse_docx_format(data: dict[str, Any]) -> DocxFormat:
    """Parse DOCX format specifications from config data."""
    docx_data = data.get("docx_format", {})
    if not isinstance(docx_data, dict):
        return DocxFormat()  # Return defaults if not present

    # Parse font sizes (optional)
    font_sizes_data = docx_data.get("font_sizes")
    font_sizes = DocxFontSizes.from_dict(font_sizes_data)

    # Parse spacing
    spacing_data = docx_data.get("spacing", {})
    spacing = DocxSpacing(
        section_before=spacing_data.get("section_before", 6),
        section_after=spacing_data.get("section_after", 2),
        role_before=spacing_data.get("role_before", 3),
        role_after=spacing_data.get("role_after", 1),
        bullet_before=spacing_data.get("bullet_before", 0),
        bullet_after=spacing_data.get("bullet_after", 1),
        name_before=spacing_data.get("name_before", 0),
        name_after=spacing_data.get("name_after", 0),
    )

    # Parse constraints (optional)
    constraints_data = docx_data.get("constraints")
    constraints = DocxConstraints.from_dict(constraints_data)

    # Parse formatting
    formatting_data = docx_data.get("formatting", {})
    formatting = DocxFormatting(
        name_bold=formatting_data.get("name_bold", True),
        section_headers_bold=formatting_data.get("section_headers_bold", True),
        section_headers_underlined=formatting_data.get("section_headers_underlined", True),
        role_headers_bold=formatting_data.get("role_headers_bold", True),
        role_headers_italics=formatting_data.get("role_headers_italics", False),
        use_bullets=formatting_data.get("use_bullets", True),
        bullet_indent_inches=formatting_data.get("bullet_indent_inches", 0.25),
    )

    return DocxFormat(
        page_size=docx_data.get("page_size", "A4"),
        page_width_inches=docx_data.get("page_dimensions", {}).get("width_inches", 8.27),
        page_height_inches=docx_data.get("page_dimensions", {}).get("height_inches", 11.69),
        margin_inches=docx_data.get("margins_inches", 0.25),
        font_family=docx_data.get("font_family", "Lora"),
        font_sizes=font_sizes,
        spacing=spacing,
        constraints=constraints,
        formatting=formatting,
    )



def load_config_from_file(config_path: str | Path) -> CVConfig:
    """Load and parse CV config from a markdown file with YAML front matter.
    
    Args:
        config_path: Path to the config file
        
    Returns:
        CVConfig object
        
    Raises:
        ConfigParseError: If file cannot be parsed or is invalid
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise ConfigParseError(f"Config file not found: {config_path}")

    try:
        content = config_path.read_text(encoding="utf-8")
    except IOError as e:
        raise ConfigParseError(f"Failed to read config file: {e}")

    yaml_content, markdown_content = _extract_yaml_front_matter(content)

    if yaml_content is None:
        raise ConfigParseError("Config file must have YAML front matter (starting with ---)")

    # Parse YAML
    data = _parse_yaml_dict(yaml_content)

    # Validate required fields
    if "page_limit" not in data:
        raise ConfigParseError("Config must have required field: page_limit")

    try:
        page_limit = int(data["page_limit"])
    except (ValueError, TypeError):
        raise ConfigParseError("page_limit must be an integer")

    if page_limit < 1 or page_limit > 3:
        raise ConfigParseError("page_limit must be between 1 and 3")

    if "style_preference" not in data:
        raise ConfigParseError("Config must have required field: style_preference")

    # Parse optional fields with defaults
    style_preference = _parse_style_preference(data)
    priorities = _parse_priorities(data)
    structure = _parse_structure(data)
    project_prioritization = _parse_project_prioritization(data)
    rules = _parse_rules(data)
    docx_format = _parse_docx_format(data)
    total_pages = int(data.get("total_pages", page_limit))

    config = CVConfig(
        page_limit=page_limit,
        total_pages=total_pages,
        style_preference=style_preference,
        docx_format=docx_format,
        priorities=priorities,
        structure=structure,
        project_prioritization=project_prioritization,
        rules=rules,
    )

    # Validate
    is_valid, errors = config.validate()
    if not is_valid:
        raise ConfigParseError(f"Config validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    return config


def create_default_config(page_limit: int = 1) -> CVConfig:
    """Create a default CVConfig with sensible defaults.
    
    Args:
        page_limit: Number of pages (1-3), defaults to 1
        
    Returns:
        CVConfig with defaults
    """
    return CVConfig(
        page_limit=max(1, min(3, page_limit)),
        style_preference=StylePreference(),
        priorities=SectionPriorities(),
        structure=StructureConfig(),
        project_prioritization=ProjectPrioritizationWeights(),
        rules=CVRules(),
    )
