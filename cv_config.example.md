---
# Required fields
page_limit: 2

style_preference:
  tone: "professional"
  detail_level: "concise"
  emphasis: "impact_metrics"

# Optional fields (uncomment to customize, otherwise defaults are used)

# Section priorities - determines what gets cut first if content exceeds page limit
# Options: HIGH, MEDIUM, LOW
priorities:
  experience: "HIGH"
  projects: "HIGH"
  skills: "MEDIUM"
  education: "MEDIUM"
  certifications: "LOW"
  awards: "LOW"

# Structure - which sections to include and in what order
structure:
  sections: ["experience", "projects", "skills", "education", "certifications"]
  # order: [0, 1, 2, 3, 4]  # Custom ordering if needed

# Project prioritization weights (must sum to ~1.0)
# Used when projects need to be cut or reordered
project_prioritization:
  technical_complexity: 0.3
  impact_metrics: 0.3
  maturity: 0.2
  keyword_relevance: 0.1
  recency: 0.1

# Rules - DOs and DONTs for CV generation
rules:
  dos:
    - "Use quantified metrics (percentages, time saved, users impacted)"
    - "Include real-world impact explanations for non-technical audiences"
    - "Action-verb-first bullets (Architected, Engineered, Optimized)"
    - "Focus on outcomes over tasks"
    - "Preserve technical depth where relevant"
  donts:
    - "Avoid buzzwords (expert, experienced, passionate)"
    - "Don't list tools without context or outcome"
    - "Don't use passive voice"
    - "Don't exceed the page limit"
    - "Don't invent metrics or facts"

---

# CV Configuration Guide

## Overview
This configuration file controls how your CV is tailored and optimized. It uses YAML front matter (between the `---` delimiters) for structured configuration, and markdown below for documentation.

## Required Fields

### `page_limit`
- **Type**: Integer (1-3)
- **Description**: Maximum number of pages for the final CV
- **Example**: `page_limit: 2`

### `style_preference`
- **Type**: Dictionary with three fields
- **Fields**:
  - `tone`: "formal" | "professional" | "casual" (how formal/casual the language should be)
  - `detail_level`: "concise" | "balanced" | "detailed" (how much detail per point)
  - `emphasis`: "impact_metrics" | "technical_depth" | "growth_trajectory" | "balanced" (what to emphasize)
- **Example**:
  ```yaml
  style_preference:
    tone: "professional"
    detail_level: "concise"
    emphasis: "impact_metrics"
  ```

## Optional Fields

### `priorities`
Controls which sections get cut first if content exceeds the page limit.
- **Type**: Dictionary with section names as keys
- **Sections**: experience, projects, skills, education, certifications, awards
- **Values**: "HIGH", "MEDIUM", or "LOW"
- **Default**: experience & projects HIGH, skills MEDIUM, others LOW
- **Example**:
  ```yaml
  priorities:
    experience: "HIGH"
    projects: "HIGH"
    skills: "MEDIUM"
  ```

### `structure`
Controls which sections appear and their order.
- **Type**: Dictionary
- **Fields**:
  - `sections`: List of section names to include
  - `order`: (Optional) Custom ordering as list of indices
- **Default**: All sections in standard order
- **Example**:
  ```yaml
  structure:
    sections: ["experience", "projects", "skills", "education"]
    order: [0, 1, 2, 3]  # Show in this order
  ```

### `project_prioritization`
Weights for intelligent project selection when cutting/reordering.
- **Type**: Dictionary with numeric weights
- **Fields**:
  - `technical_complexity`: How technically challenging the project is
  - `impact_metrics`: Presence of quantified impact (users, time saved, etc.)
  - `maturity`: How established/finished the project is
  - `keyword_relevance`: How well it matches target job keywords
  - `recency`: How recent the project is
- **Constraint**: Weights should sum to ~1.0 (they'll be normalized)
- **Default**: complexity 0.3, impact 0.3, maturity 0.2, keywords 0.1, recency 0.1
- **Example**:
  ```yaml
  project_prioritization:
    technical_complexity: 0.35
    impact_metrics: 0.35
    maturity: 0.15
    keyword_relevance: 0.10
    recency: 0.05
  ```

### `rules`
DOs and DONTs to guide AI optimization.
- **Type**: Dictionary with `dos` and `donts` lists
- **Example**:
  ```yaml
  rules:
    dos:
      - "Use quantified metrics"
      - "Focus on business impact"
    donts:
      - "Avoid buzzwords"
      - "Don't exceed page limit"
  ```

## Common Scenarios

### Scenario 1: Academic Focus
```yaml
page_limit: 1
style_preference:
  tone: "formal"
  detail_level: "balanced"
  emphasis: "technical_depth"
priorities:
  education: "HIGH"
  projects: "HIGH"
  experience: "MEDIUM"
```

### Scenario 2: Impact-Driven Startup Role
```yaml
page_limit: 2
style_preference:
  tone: "professional"
  detail_level: "concise"
  emphasis: "impact_metrics"
priorities:
  projects: "HIGH"
  experience: "HIGH"
  skills: "MEDIUM"
project_prioritization:
  impact_metrics: 0.4
  technical_complexity: 0.3
  recency: 0.2
  maturity: 0.05
  keyword_relevance: 0.05
```

### Scenario 3: Career Transition (Show Growth)
```yaml
page_limit: 2
style_preference:
  tone: "professional"
  detail_level: "balanced"
  emphasis: "growth_trajectory"
priorities:
  projects: "HIGH"
  experience: "HIGH"
  education: "MEDIUM"
project_prioritization:
  keyword_relevance: 0.35
  impact_metrics: 0.25
  technical_complexity: 0.25
  recency: 0.10
  maturity: 0.05
```

## Tips

- **For strict 1-page CVs**: Set `page_limit: 1` and `detail_level: concise`, with high priorities on the most relevant sections
- **For 2-page CVs**: You can include more projects and education details
- **For project prioritization**: Higher weight on `impact_metrics` if applying to metric-focused roles (product, data science), higher on `technical_complexity` for engineering roles
- **Real-world impact**: The AI will automatically translate technical achievements into business/user impact (e.g., "Database optimization" → "Made the app 5x faster for 50K daily users")
