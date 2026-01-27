"""
Convert a DOCX CV to the JSON format expected by the AI CV Builder.

Usage:
    python scripts/docx_to_json.py "CV of Aariz Waqas (1).docx" --output my_cv.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from docx import Document


def _extract_paragraphs(doc_path: str) -> list[str]:
    doc = Document(doc_path)
    return [p.text.strip() for p in doc.paragraphs]


def _parse_contact_line(line: str) -> dict:
    contact = {"links": []}
    
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", line)
    if email_match:
        contact["email"] = email_match.group(0)
    
    phone_match = re.search(r"\+[\d\s]+", line)
    if phone_match:
        contact["phone"] = phone_match.group(0).strip()
    
    return contact


def _parse_links(lines: list[str], start_idx: int) -> tuple[list[dict], int]:
    links = []
    idx = start_idx
    
    while idx < len(lines):
        line = lines[idx]
        if not line or line.isupper():
            break
        
        # Check for URLs
        url_patterns = [
            (r"FlexiDiet:\s*(https?://[^\s|]+)", "FlexiDiet"),
            (r"Github:\s*(https?://[^\s|]+)", "GitHub"),
            (r"LinkedIn:\s*(https?://[^\s|]+)", "LinkedIn"),
        ]
        
        for pattern, label in url_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                links.append({"label": label, "url": match.group(1).strip()})
        
        # Generic URL extraction
        if not any(re.search(p[0], line, re.IGNORECASE) for p in url_patterns):
            urls = re.findall(r"https?://[^\s]+", line)
            for url in urls:
                label = "Website"
                if "github" in url.lower():
                    label = "GitHub"
                elif "linkedin" in url.lower():
                    label = "LinkedIn"
                links.append({"label": label, "url": url.strip()})
        
        idx += 1
    
    return links, idx


def _find_section(paragraphs: list[str], section_name: str) -> int:
    for i, p in enumerate(paragraphs):
        if p.strip().upper().startswith(section_name.upper()):
            return i
    return -1


def _parse_education(paragraphs: list[str], start_idx: int) -> tuple[list[dict], int]:
    education = []
    idx = start_idx + 1
    
    while idx < len(paragraphs):
        line = paragraphs[idx].strip()
        if not line:
            idx += 1
            continue
        if line.isupper() or line.upper().startswith("TECHNICAL"):
            break
        
        # Parse education line: "University - Degree    Dates"
        match = re.match(r"(.+?)\s*-\s*(.+?)\s*(\d{4}\s*-\s*\d{4}|\d{4}\s*-\s*Present)?$", line)
        if match:
            school = match.group(1).strip()
            degree = match.group(2).strip()
            dates = match.group(3).strip() if match.group(3) else ""
            # Clean up tabs from dates
            dates = re.sub(r"\s+", " ", dates).strip()
            if "\t" in line:
                parts = line.split("\t")
                dates = parts[-1].strip() if len(parts) > 1 else dates
            
            education.append({
                "school": school,
                "degree": degree,
                "location": "",
                "dates": dates,
                "details": []
            })
        
        idx += 1
    
    return education, idx


def _parse_skills(paragraphs: list[str], start_idx: int) -> tuple[dict, int]:
    groups = []
    idx = start_idx + 1
    
    while idx < len(paragraphs):
        line = paragraphs[idx].strip()
        if not line:
            idx += 1
            continue
        if line.isupper() and "SKILL" not in line.upper():
            break
        
        # Parse "Category: item1, item2, item3"
        if ":" in line:
            parts = line.split(":", 1)
            name = parts[0].strip()
            items = [item.strip() for item in parts[1].split(",") if item.strip()]
            if items:
                groups.append({"name": name, "items": items})
        
        idx += 1
    
    return {"groups": groups}, idx


def _parse_experience(paragraphs: list[str], start_idx: int) -> tuple[list[dict], int]:
    experiences = []
    idx = start_idx + 1
    current_exp = None
    
    while idx < len(paragraphs):
        line = paragraphs[idx].strip()
        
        if not line:
            idx += 1
            continue
        
        # Check for section end
        if line.isupper() and ("HIGHLIGHT" in line.upper() or "PROJECT" in line.upper()):
            break
        
        # Check if this is a job title line (contains company and dates)
        job_match = re.match(
            r"(.+?)\s*-\s*(.+?)\s+(Remote|On-site|Hybrid)?\s*\|\s*(.+)$",
            line,
            re.IGNORECASE
        )
        
        if job_match:
            if current_exp:
                experiences.append(current_exp)
            
            role = job_match.group(1).strip()
            company = job_match.group(2).strip()
            location = job_match.group(3).strip() if job_match.group(3) else "Remote"
            dates = job_match.group(4).strip()
            
            current_exp = {
                "company": company,
                "role": role,
                "location": location,
                "dates": dates,
                "bullets": []
            }
        elif current_exp and line and not line.isupper():
            # This is a bullet point
            current_exp["bullets"].append(line)
        
        idx += 1
    
    if current_exp:
        experiences.append(current_exp)
    
    return experiences, idx


def _parse_projects(paragraphs: list[str], start_idx: int) -> list[dict]:
    projects = []
    idx = start_idx + 1
    current_project = None
    
    while idx < len(paragraphs):
        line = paragraphs[idx].strip()
        
        if not line:
            idx += 1
            continue
        
        # Check for new section
        if line.isupper() and idx > start_idx + 1:
            break
        
        # Project titles are usually short and don't contain certain patterns
        is_title = (
            len(line) < 100 and
            not line.startswith("Tech:") and
            not line.startswith("Built") and
            not line.startswith("Created") and
            not line.startswith("Designed") and
            not line.startswith("Production") and
            "%" not in line
        )
        
        if is_title and not current_project:
            current_project = {
                "name": line,
                "link": "",
                "dates": "",
                "bullets": []
            }
        elif is_title and current_project and len(current_project["bullets"]) > 0:
            # New project
            projects.append(current_project)
            current_project = {
                "name": line,
                "link": "",
                "dates": "",
                "bullets": []
            }
        elif current_project:
            # Tech stack or description
            if line.startswith("Tech:"):
                current_project["bullets"].append(line)
            else:
                # Split long descriptions into sentences if needed
                current_project["bullets"].append(line)
        
        idx += 1
    
    if current_project:
        projects.append(current_project)
    
    return projects


def _parse_highlights(paragraphs: list[str], start_idx: int) -> tuple[list[str], int]:
    highlights = []
    idx = start_idx + 1
    
    while idx < len(paragraphs):
        line = paragraphs[idx].strip()
        
        if not line:
            idx += 1
            continue
        
        if line.isupper():
            break
        
        highlights.append(line)
        idx += 1
    
    return highlights, idx


def convert_docx_to_json(docx_path: str) -> dict:
    paragraphs = _extract_paragraphs(docx_path)
    
    # Extract name (first non-empty line)
    name = ""
    for p in paragraphs:
        if p:
            name = p
            break
    
    # Extract contact info
    contact = {"email": "", "phone": "", "location": "", "links": []}
    for i, p in enumerate(paragraphs[1:5], 1):
        if "email" in p.lower() or "@" in p:
            contact.update(_parse_contact_line(p))
        if "http" in p.lower():
            links, _ = _parse_links(paragraphs, i)
            contact["links"].extend(links)
    
    # Remove duplicate links
    seen_urls = set()
    unique_links = []
    for link in contact["links"]:
        if link["url"] not in seen_urls:
            seen_urls.add(link["url"])
            unique_links.append(link)
    contact["links"] = unique_links
    
    # Find and parse sections
    profile_idx = _find_section(paragraphs, "PROFILE")
    edu_idx = _find_section(paragraphs, "EDUCATION")
    skills_idx = _find_section(paragraphs, "TECHNICAL SKILLS")
    exp_idx = _find_section(paragraphs, "EXPERIENCE")
    highlights_idx = _find_section(paragraphs, "TECHNICAL HIGHLIGHTS")
    projects_idx = _find_section(paragraphs, "PROJECTS")
    
    # Extract summary from PROFILE section
    summary = []
    if profile_idx >= 0:
        idx = profile_idx + 1
        while idx < len(paragraphs) and not paragraphs[idx].strip().isupper():
            if paragraphs[idx].strip():
                summary.append(paragraphs[idx].strip())
            idx += 1
    
    # Parse education
    education = []
    if edu_idx >= 0:
        education, _ = _parse_education(paragraphs, edu_idx)
    
    # Parse skills
    skills = {"groups": []}
    if skills_idx >= 0:
        skills, _ = _parse_skills(paragraphs, skills_idx)
    
    # Parse experience
    experience = []
    if exp_idx >= 0:
        experience, _ = _parse_experience(paragraphs, exp_idx)
    
    # Parse highlights and add to summary
    if highlights_idx >= 0:
        highlights, _ = _parse_highlights(paragraphs, highlights_idx)
        summary.extend(highlights)
    
    # Parse projects
    projects = []
    if projects_idx >= 0:
        projects = _parse_projects(paragraphs, projects_idx)
    
    # Determine title from experience or profile
    title = ""
    if experience:
        title = experience[0].get("role", "")
    elif summary:
        # Try to extract title from summary
        for s in summary:
            if "developer" in s.lower() or "engineer" in s.lower():
                match = re.search(r"([\w\s]+Developer|[\w\s]+Engineer)", s, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    break
    
    return {
        "name": name,
        "title": title,
        "contact": contact,
        "summary": summary,
        "experience": experience,
        "projects": projects,
        "education": education,
        "skills": skills,
        "certifications": [],
        "awards": []
    }


def main():
    parser = argparse.ArgumentParser(description="Convert DOCX CV to JSON format")
    parser.add_argument("input", help="Path to input DOCX file")
    parser.add_argument("--output", "-o", required=True, help="Path to output JSON file")
    
    args = parser.parse_args()
    
    if not Path(args.input).exists():
        print(f"Error: File not found: {args.input}")
        return 1
    
    cv_json = convert_docx_to_json(args.input)
    
    Path(args.output).write_text(
        json.dumps(cv_json, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    print(f"Converted CV saved to: {args.output}")
    return 0


if __name__ == "__main__":
    exit(main())
