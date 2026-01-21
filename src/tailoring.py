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
4. Include specific numbers, percentages, and metrics wherever possible.
5. Keep content concise but PRESERVE ALL CONTENT - this CV should fit on ONE PAGE through better writing, not deletion.
6. NEVER remove projects, experience, or achievements from the original CV.
""".strip()


def _build_user_prompt(cv_json: dict, readmes: dict[str, str]) -> str:
    readme_blocks = []
    for name, content in readmes.items():
        trimmed = content[:12000]
        readme_blocks.append(f"### {name}\n{trimmed}")

    readme_text = "\n\n".join(readme_blocks) if readme_blocks else "(No README content provided.)"

    return f"""
Input CV (JSON):
{json.dumps(cv_json, ensure_ascii=False)}

Repository READMEs (for ENHANCING and TAILORING the CV - these provide additional context):
{readme_text}

=== CRITICAL RULES - READ FIRST ===

⚠️ PRESERVE ALL ORIGINAL CONTENT:
- Keep ALL projects from the input CV - do NOT remove any projects
- Keep ALL experience bullets - you may rewrite them but not delete them
- Keep ALL skills - you may reorganize but not remove
- The READMEs are for ENHANCEMENT and adding context, NOT for replacing existing content
- If a project is in the input CV but not in the READMEs, it MUST still appear in the output

⚠️ ENHANCE, DON'T DELETE:
- Use README content to ADD technical depth and keywords to matching projects
- Improve wording and add metrics, but preserve the substance
- Condense through better writing, not by removing content

=== YOUR TASK ===

Create an AWARD-WINNING, ATS-OPTIMIZED CV by following these expert guidelines:

## 1. PROFILE/SUMMARY (2-3 sentences MAX)
- Lead with years of experience + core expertise
- Include 2-3 most impressive quantified achievements
- Pack with ATS keywords naturally
- Example: "AI/ML Engineer with 2+ years building production RAG systems and LLM applications. Improved retrieval accuracy by 60% and reduced token costs by 40% across enterprise deployments. Expert in Python, LangChain, LlamaIndex, and cloud-native AI infrastructure."

## 2. EXPERIENCE BULLETS (keep ALL bullets, rewrite for impact)
- Formula: [ACTION VERB] + [WHAT you did] + [HOW/using what] + [RESULT with NUMBER]
- Start with the STRONGEST, most relevant achievements
- Use power verbs: Architected, Engineered, Optimized, Reduced, Increased, Deployed, Automated, Scaled
- ALWAYS include metrics: percentages, time saved, users impacted, cost reduction, performance gains
- Bad: "Worked on AI systems"
- Good: "Architected RAG pipeline using LlamaIndex, achieving 60% improvement in retrieval accuracy and 3x faster document lookup"

## 3. PROJECTS (Keep ALL projects from input CV)
- Format each as: "[One powerful sentence: what it does + key metric/achievement + tech stack]"
- Keep each project to 2-3 sentences maximum but include key details
- Focus on IMPACT and RESULTS while preserving important technical details
- Use README content to enhance projects that match, but keep non-README projects too
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

## 7. ATS KEYWORD INJECTION
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

FINAL CHECK: Count projects in input vs output - they MUST match. Do not drop any content.
""".strip()


def _extract_json(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in model response.")
        return json.loads(match.group(0))


def tailor_cv(cv_json: dict, readmes: dict[str, str], config: OpenRouterConfig) -> dict:
    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(cv_json, readmes)},
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

    response = requests.post(
        f"{config.base_url}/chat/completions",
        headers=headers,
        json=payload,
        timeout=300,
    )

    if not response.ok:
        raise ValueError(f"OpenRouter error: {response.status_code} {response.text}")

    data = response.json()
    content = data["choices"][0]["message"]["content"]
    return _extract_json(content)
