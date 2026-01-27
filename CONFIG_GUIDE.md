# CV Configuration & Intelligent Optimization Guide

## Overview

The CV Builder now supports **intelligent, config-driven CV optimization** with page-aware content management. You can:

1. **Configure CV behavior** through a markdown config file with your priorities, structure, and rules
2. **Automatically fit CVs to page limits** (1, 2, or 3 pages) with intelligent content removal
3. **Review all changes** before finalizing, with the ability to steer the AI in different directions
4. **Get detailed reports** of what changed and why

## Quick Start

### 1. Create Your Config File

Copy the example config and customize it:

```bash
cp cv_config.example.md my_cv_config.md
```

Edit `my_cv_config.md`:

```yaml
---
page_limit: 1
style_preference:
  tone: "professional"
  detail_level: "concise"
  emphasis: "impact_metrics"
priorities:
  experience: "HIGH"
  projects: "HIGH"
  skills: "MEDIUM"
---
```

### 2. Build CV with Config

```bash
./run.ps1 build --cv my_cv.json --config my_cv_config.md --output-docx output.docx
```

Or manually:

```bash
python -m src.main build \
  --cv my_cv.json \
  --config my_cv_config.md \
  --output-docx output.docx
```

## Configuration File Format

Config files use **Markdown with YAML front matter**:

```markdown
---
# YAML front matter here (between ---)
page_limit: 2
style_preference:
  tone: "professional"
  detail_level: "concise"
  emphasis: "impact_metrics"
---

# Markdown documentation below (optional)
This section is for your notes and doesn't affect behavior.
```

### Required Fields

#### `page_limit`
- **Type**: Integer (1, 2, or 3)
- **Description**: Target number of pages for your CV
- **Example**: `page_limit: 1`

#### `style_preference`
Dictionary with three sub-fields:

- **`tone`**: How formal the language should be
  - Options: `"formal"`, `"professional"`, `"casual"`
  - Example: `tone: "professional"`

- **`detail_level`**: How much detail to include
  - Options: `"concise"`, `"balanced"`, `"detailed"`
  - Example: `detail_level: "concise"`

- **`emphasis`**: What to emphasize in achievements
  - Options: `"impact_metrics"`, `"technical_depth"`, `"growth_trajectory"`, `"balanced"`
  - Example: `emphasis: "impact_metrics"`

Full example:

```yaml
style_preference:
  tone: "professional"
  detail_level: "concise"
  emphasis: "impact_metrics"
```

### Optional Fields

#### `priorities`
Controls which sections are cut first if content exceeds page limit.

```yaml
priorities:
  experience: "HIGH"
  projects: "HIGH"
  skills: "MEDIUM"
  education: "MEDIUM"
  certifications: "LOW"
  awards: "LOW"
```

Values: `"HIGH"`, `"MEDIUM"`, `"LOW"`

**Default** (if not specified):
```
experience: HIGH
projects: HIGH
skills: MEDIUM
education: MEDIUM
certifications: LOW
awards: LOW
```

#### `structure`
Which sections to include and their order.

```yaml
structure:
  sections: ["experience", "projects", "skills", "education"]
  # order: [0, 1, 2, 3]  # Optional custom ordering
```

#### `project_prioritization`
Weights for choosing which projects to keep (if trimming is needed).

```yaml
project_prioritization:
  technical_complexity: 0.3      # How technically challenging
  impact_metrics: 0.3            # Has quantified impact (users, time saved, etc)
  maturity: 0.2                  # How established/finished
  keyword_relevance: 0.1         # Matches job keywords
  recency: 0.1                   # How recent
```

**Important**: Weights should sum to ~1.0 (will be normalized)

#### `rules`
DOs and DONTs to guide AI optimization.

```yaml
rules:
  dos:
    - "Use quantified metrics (percentages, time saved, users impacted)"
    - "Include real-world impact explanations"
    - "Action-verb-first bullets"
  donts:
    - "Avoid buzzwords"
    - "Don't list tools without context"
```

## How Optimization Works

### Page Detection & Content Reduction

When your CV exceeds the page limit:

1. **Detects current page length** by analyzing document structure and content density
2. **Calculates words to remove** based on target page limit
3. **Removes items by priority**:
   - Lowest-priority sections first (e.g., certifications → awards → education → skills)
   - Within sections, removes newest/less important items while preserving at least one item per section
4. **Condenses remaining content**:
   - Removes redundant phrases
   - Tightens wording
   - Removes filler language
5. **Adds real-world impact language**:
   - Translates technical terms into business impact
   - Example: "Optimized database queries" → "made the app faster for 50K daily users"
6. **Fills space optimally**:
   - Adjusts margins and spacing
   - Expands remaining content if needed to fill page

### Change Tracking & Review

All changes are tracked with:
- **What changed** (removed item, condensed bullet, etc.)
- **Why it changed** (reasoning from priorities)
- **Impact** (words saved, importance level)

Changes are displayed in the terminal and saved to `changes/` folder:
- `cv_optimization_summary.md` - Human-readable overview
- `cv_optimization_detailed.json` - Machine-readable details
- `cv_optimization_summary.txt` - Plain text summary

### Real-World Impact Translation

The builder automatically adds business-oriented language:

| Technical | → | Real-World Impact |
|-----------|---|------------------|
| "Optimized database queries" | → | "made the app faster for users" |
| "Scaled infrastructure" | → | "supported growth to 100K users" |
| "Implemented CI/CD" | → | "deployed changes faster and safer" |
| "Improved uptime" | → | "reduced service interruptions" |

## Configuration Examples

### Example 1: Strict 1-Page CV

Perfect for one-page resume requirements:

```yaml
---
page_limit: 1
style_preference:
  tone: "professional"
  detail_level: "concise"
  emphasis: "impact_metrics"
priorities:
  experience: "HIGH"
  projects: "MEDIUM"
  skills: "MEDIUM"
  education: "LOW"
  certifications: "LOW"
  awards: "LOW"
---
```

### Example 2: Impact-Driven (Data Science Role)

Emphasize metrics and impact:

```yaml
---
page_limit: 2
style_preference:
  tone: "professional"
  detail_level: "balanced"
  emphasis: "impact_metrics"
priorities:
  projects: "HIGH"
  experience: "HIGH"
  skills: "HIGH"
  education: "MEDIUM"
project_prioritization:
  impact_metrics: 0.4
  technical_complexity: 0.3
  keyword_relevance: 0.2
  maturity: 0.05
  recency: 0.05
---
```

### Example 3: Technical Depth (Senior Engineer)

Highlight technical skills and complexity:

```yaml
---
page_limit: 2
style_preference:
  tone: "professional"
  detail_level: "detailed"
  emphasis: "technical_depth"
priorities:
  experience: "HIGH"
  projects: "HIGH"
  skills: "HIGH"
  education: "MEDIUM"
project_prioritization:
  technical_complexity: 0.4
  impact_metrics: 0.3
  keyword_relevance: 0.15
  maturity: 0.1
  recency: 0.05
---
```

### Example 4: Career Transition (Emphasize Growth)

Show learning trajectory:

```yaml
---
page_limit: 2
style_preference:
  tone: "professional"
  detail_level: "balanced"
  emphasis: "growth_trajectory"
priorities:
  projects: "HIGH"
  experience: "HIGH"
  education: "HIGH"
  skills: "MEDIUM"
project_prioritization:
  keyword_relevance: 0.3
  technical_complexity: 0.3
  impact_metrics: 0.2
  recency: 0.15
  maturity: 0.05
---
```

## Usage Commands

### Build with Config File

```bash
python -m src.main build \
  --cv my_cv.json \
  --config my_cv_config.md \
  --output-docx output.docx \
  --output-json output.json
```

### Interactive Mode with Config

```bash
python -m src.main interactive \
  --cv my_cv.json \
  --repos repos.txt \
  --config my_cv_config.md \
  --output-docx output.docx
```

## Change Reports

After optimization, three reports are saved:

### 1. Text Summary (`summary.txt`)
```
=======================================================================
CV OPTIMIZATION CHANGES REPORT
=======================================================================

Generated: 2026-01-27T13:22:45

SUMMARY
-------
Total Changes: 4
Words Saved: 202

CHANGES BY TYPE
-------
Removed: 2
Condensed: 2

CHANGES BY SECTION
-------
Projects: 2
Experience: 2
```

### 2. Markdown Summary (`summary.md`)
Human-friendly with formatted sections, perfect for reviewing in your editor.

### 3. Detailed JSON (`detailed.json`)
Machine-readable with before/after content for each change:

```json
{
  "timestamp": "2026-01-27T13:22:45.641Z",
  "summary": {
    "total_changes": 4,
    "total_words_saved": 202,
    ...
  },
  "changes": [
    {
      "change_type": "removed",
      "section": "projects",
      "item_key": "project_2",
      "before_content": "Built visualization dashboard...",
      "after_content": "",
      "reason": "Lower priority item removed to reduce content",
      "words_saved": 45
    },
    ...
  ]
}
```

## Tips & Best Practices

### For Strict Page Limits

1. **Set correct `page_limit`** in config - this is critical
2. **Prioritize strategically** - keep what matters most for your target role
3. **Use concise `detail_level`** to maximize space for high-priority content
4. **Review changes** before finalizing - sometimes manual tweaks are needed

### For Best Impact Statements

1. **Include metrics** in your original bullets when possible
2. **Mention users/scope** (e.g., "100K users", "finance team") for better translations
3. **Use action verbs** that clearly show impact
4. **Avoid passive voice** in original content

### Project Prioritization Tuning

- **Data Science/Analytics roles**: Increase `impact_metrics` weight (0.3-0.4)
- **Senior Engineering roles**: Increase `technical_complexity` weight (0.3-0.4)
- **Career transitions**: Increase `keyword_relevance` weight (0.3-0.4)
- **Startup roles**: Balance all factors, emphasize recency (recent projects first)

## Troubleshooting

### Config file not loading
```
Error: Config file not found
```
Make sure path is correct and file starts with `---`

### Page limit not being respected
- Check that `page_limit` is correctly set (1-3)
- Verify section `priorities` are set correctly
- Check `detail_level` - "concise" works better than "detailed" for tight limits

### Missing real-world impact translations
- Ensure your original bullets have enough context
- Use specific metrics and user counts
- Check that impact_translator.py is included in build

## Future Enhancements

- Job description matching for automatic keyword prioritization
- Multi-CV generation with different configs for different roles
- ATS score predictions before/after optimization
- Interactive steering of AI during optimization
- Custom section templates and ordering

## See Also

- [Config File Example](cv_config.example.md)
- [Main README](README.md)
