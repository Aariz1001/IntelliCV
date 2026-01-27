from __future__ import annotations

import json
import re
from typing import Any

import requests

from .config import OpenRouterConfig


SYSTEM_PROMPT = """
You are a world-class technical resume writer and career coach who has helped thousands of engineers land jobs at top tech companies (FAANG, startups, Fortune 500).

Your expertise includes:
- ATS (Applicant Tracking System) optimization
- Quantified impact statements with metrics
- Action-verb-first bullet points
- Keyword density for technical roles
- Concise, high-impact writing

Rules:
1. Return ONLY valid JSON matching the provided schema.
2. No markdown, commentary, or extra keys.
3. Every bullet must start with a strong action verb.
4. Include specific numbers, percentages, and metrics wherever possible, but NEVER invent them.
5. Preserve the original CV structure and ordering unless explicitly asked to reorder.
6. Keep content concise but PRESERVE ALL CONTENT - this CV should fit on ONE PAGE through better writing, not deletion.
7. NEVER remove projects, experience, or achievements from the original CV.
8. Minimize changes to existing wording; prefer light tightening over rewrites.
9. If additional repo projects are requested, include them while keeping all originals, condensing and prioritizing by credibility/impressiveness.
10. Follow user guidance when provided, but never violate these rules or invent facts.
""".strip()


def _format_inventory_list(items: list[str]) -> str:
    if not items:
        return "(none)"
    return "\n".join(f"- {item}" for item in items)


def _build_cv_inventory(cv_json: dict) -> str:
    name = (cv_json.get("name") or "").strip()
    title = (cv_json.get("title") or "").strip()
    summary = cv_json.get("summary", []) or []
    experience = cv_json.get("experience", []) or []
    projects = cv_json.get("projects", []) or []
    education = cv_json.get("education", []) or []
    skills_groups = cv_json.get("skills", {}).get("groups", []) or []

    experience_lines = []
    for item in experience:
        role = item.get("role", "")
        company = item.get("company", "")
        dates = item.get("dates", "")
        location = item.get("location", "")
        header_parts = [part for part in [role, company] if part]
        header = " — ".join(header_parts) if header_parts else "Experience entry"
        if dates:
            header = f"{header} ({dates})"
        if location:
            header = f"{header}, {location}"
        bullet_count = len(item.get("bullets", []))
        experience_lines.append(f"{header} | bullets: {bullet_count}")

    project_lines = []
    for item in projects:
        project_name = item.get("name", "") or "Project"
        dates = item.get("dates", "")
        link = item.get("link", "")
        bullet_count = len(item.get("bullets", []))
        line = project_name
        if dates:
            line = f"{line} ({dates})"
        if link:
            line = f"{line} | link: {link}"
        line = f"{line} | bullets: {bullet_count}"
        project_lines.append(line)

    skills_lines = []
    for group in skills_groups:
        group_name = group.get("name", "") or "Group"
        items = group.get("items", []) or []
        skills_lines.append(f"{group_name}: {len(items)} items")

    return "\n".join(
        [
            f"Name: {name or '(missing)'}",
            f"Title: {title or '(missing)'}",
            f"Summary bullets: {len(summary)}",
            f"Experience entries: {len(experience)}",
            "Experience list:\n" + _format_inventory_list(experience_lines),
            f"Project entries: {len(projects)}",
            "Project list:\n" + _format_inventory_list(project_lines),
            f"Education entries: {len(education)}",
            f"Skill groups: {len(skills_groups)}",
            "Skill groups list:\n" + _format_inventory_list(skills_lines),
        ]
    )


def _build_user_prompt(cv_json: dict, readmes: dict[str, str], guidance: str | None) -> str:
    readme_blocks = []
    for name, content in readmes.items():
        trimmed = content[:12000]
        readme_blocks.append(f"### {name}\n{trimmed}")

    readme_text = "\n\n".join(readme_blocks) if readme_blocks else "(No README content provided.)"
    guidance_text = guidance.strip() if guidance else ""
    inventory_text = _build_cv_inventory(cv_json)

    return f"""
CV Inventory (for grounding; do NOT output this section):
{inventory_text}

User Guidance (optional; apply if compatible with critical rules):
{guidance_text or "(none)"}

Input CV (JSON):
{json.dumps(cv_json, ensure_ascii=False)}

Repository READMEs (for ENHANCING and TAILORING the CV - these provide additional context):
{readme_text}

=== CRITICAL RULES - READ FIRST ===

[!] PRESERVE STRUCTURE & ORDER:
- Keep the same section order as the input CV
- Keep the order of experience entries and bullets
- Keep the order of existing projects unless adding new repo projects

[!] PRESERVE ALL ORIGINAL CONTENT:
- Keep ALL projects from the input CV - do NOT remove any projects
- Keep ALL experience bullets - you may rewrite them but not delete them
- Keep ALL skills - you may reorganize but not remove
- The READMEs are for ENHANCEMENT and adding context, NOT for replacing existing content
- If a project is in the input CV but not in the READMEs, it MUST still appear in the output

[!] MINIMAL CHANGES:
- Keep wording close to the original; prefer light tightening over rewrites
- Do NOT invent facts or metrics not present in the CV or READMEs
- Condense by removing redundancy, not by deleting items

[!] ENHANCE, DON'T DELETE:
- Use README content to ADD technical depth and keywords to matching projects
- If a README represents a project not in the CV, ADD it as an extra project entry
- Improve wording and add metrics when provided, but preserve the substance
- Condense through better writing, not by removing content

=== YOUR TASK ===

Create an AWARD-WINNING, ATS-OPTIMIZED CV by following these expert guidelines:

## 1. PROFILE/SUMMARY (2-3 sentences MAX)
- Lead with years of experience + core expertise
- Include 2-3 most impressive quantified achievements
- Pack with ATS keywords naturally
- Example: "AI/ML Engineer with 2+ years building production RAG systems and LLM applications. Improved retrieval accuracy by 60% and reduced token costs by 40% across enterprise deployments. Expert in Python, LangChain, LlamaIndex, and cloud-native AI infrastructure."

## 2. EXPERIENCE BULLETS (keep ALL bullets, preserve order, minimal edits)
- Formula: [ACTION VERB] + [WHAT you did] + [HOW/using what] + [RESULT with NUMBER]
- Use power verbs: Architected, Engineered, Optimized, Reduced, Increased, Deployed, Automated, Scaled
- Use existing metrics; NEVER invent numbers
- Bad: "Worked on AI systems"
- Good: "Architected RAG pipeline using LlamaIndex, achieving 60% improvement in retrieval accuracy and 3x faster document lookup"

## 3. PROJECTS (Keep ALL projects from input CV)
- Format each as: "[One powerful sentence: what it does + key metric/achievement + tech stack]"
- Keep each project to 1-2 sentences maximum but include key details
- Focus on IMPACT and RESULTS while preserving important technical details
- Use README content to enhance projects that match, but keep non-README projects too
- If extra repo projects are added, keep ALL originals and order projects by credibility/impressiveness
- Example: "Production AI diet app featuring Gemini-powered meal planning with multi-agent conversations for progress insights, achieving 30% token efficiency through structured JSON outputs. Built with Flutter, Firebase, GCP, and Python Cloud Functions."

## 4. SKILLS (ATS-OPTIMIZED - keep all, add more from READMEs)
- Group logically: Languages, Frameworks, AI/ML, Cloud, Tools
- Include EXACT technology names that ATS systems scan for
- ADD skills inferred from READMEs to existing skills
- Include variations: "Python", "LangChain", "LlamaIndex", "RAG", "Vector Search", "GCP", "Firebase"

## 5. EDUCATION (One line)
- Just: Degree — University | Dates
- No extra details unless honors/awards

## 6. SPACE-SAVING TECHNIQUES (without losing content)
- Combine related bullets where logical
- Remove redundant words like "Successfully", "Responsible for", "Helped to"
- Use symbols: & instead of "and", numbers instead of words
- Abbreviate where standard: ML, AI, LLM, RAG, API, GCP, AWS
- Tighten sentences: "Built and deployed" → "Deployed"

## 7. ATS KEYWORD INJECTION (only when supported by CV/README content)
Naturally incorporate these high-value keywords based on the content:
- Technical: Python, AI, ML, LLM, RAG, NLP, API, Cloud, DevOps, CI/CD
- Frameworks: LangChain, LlamaIndex, TensorFlow, PyTorch, FastAPI, Flask
- Cloud: GCP, AWS, Azure, Firebase, Kubernetes, Docker
- Practices: Agile, Scrum, Production, Scalable, Enterprise
- Impact words: Reduced, Increased, Improved, Optimized, Automated, Deployed

=== OUTPUT FORMAT ===

Return JSON matching this schema. For projects, put the project description as a SINGLE string in bullets[0]:

{{
  "name": "string",
  "title": "string (ATS-friendly job title)",
  "contact": {{
    "email": "string",
    "phone": "string",
    "location": "string",
    "links": [{{"label": "string", "url": "string"}}]
  }},
  "summary": ["string (2-3 sentences combined, keyword-rich)"],
  "experience": [{{
    "company": "string",
    "role": "string",
    "location": "string",
    "dates": "string",
    "bullets": ["string (ALL original bullets, rewritten with metrics)"]
  }}],
  "projects": [{{
    "name": "string",
    "link": "string",
    "dates": "string",
    "bullets": ["string (2-3 sentence paragraph: description + impact + tech stack)"]
  }}],
  "education": [{{
    "school": "string",
    "degree": "string",
    "location": "string",
    "dates": "string",
    "details": []
  }}],
  "skills": {{
    "groups": [{{"name": "string", "items": ["string (keep all + add from READMEs)"]}}]
  }},
  "certifications": ["string"],
  "awards": ["string"]
}}

FINAL CHECK: All input projects must appear in output. If extra repo projects are added, output count can exceed input. Do not drop any content.
""".strip()


def _extract_json(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in model response.")
        return json.loads(match.group(0))


def tailor_cv(
    cv_json: dict,
    readmes: dict[str, str],
    config: OpenRouterConfig,
    guidance: str | None = None,
) -> dict:
    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(cv_json, readmes, guidance)},
        ],
        "temperature": 1.0,
        "reasoning": {"effort": config.reasoning_effort},
    }

    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }
    if config.http_referer:
        headers["HTTP-Referer"] = config.http_referer
    if config.x_title:
        headers["X-Title"] = config.x_title

    import sys
    print(f"[tailoring] Calling {config.model} with {config.reasoning_effort} reasoning...", file=sys.stderr, flush=True)
    response = requests.post(
        f"{config.base_url}/chat/completions",
        headers=headers,
        json=payload,
        timeout=300,
    )
    print(f"[tailoring] API response received: {response.status_code}", file=sys.stderr, flush=True)

    if not response.ok:
        raise ValueError(f"OpenRouter error: {response.status_code} {response.text}")

    data = response.json()
    content = data["choices"][0]["message"]["content"]
    print(f"[tailoring] Extracting JSON from response...", file=sys.stderr, flush=True)
    return _extract_json(content)
