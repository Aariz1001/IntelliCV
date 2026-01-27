"""Convert tailored CV and job postings to structured JSON format."""

from __future__ import annotations

import asyncio
import json
import os
import re
from pathlib import Path
from typing import Any, Dict

import httpx
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .content_ingestor import ContentIngestor


console = Console()


class CVToJSONConverter:
    """Converts CV text to structured JSON using AI."""
    
    def __init__(self, api_key: str | None = None):
        """Initialize converter with OpenRouter API key."""
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key required. Set OPENROUTER_API_KEY environment variable."
            )
        
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(60.0))
    
    async def _query_llm(self, prompt: str, system_prompt: str) -> str:
        """Query LLM for structured extraction.
        
        Args:
            prompt: The main prompt with content to extract
            system_prompt: System instructions
            
        Returns:
            JSON string response
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "google/gemini-3-flash-preview",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }
        
        try:
            response = await self.client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            console.print(f"[bold red]Error querying LLM:[/bold red] {e}")
            raise
    
    async def extract_cv_json(self, cv_text: str) -> Dict[str, Any]:
        """Extract structured CV data from text.
        
        Args:
            cv_text: Raw CV text
            
        Returns:
            Structured CV data as dictionary
        """
        system_prompt = """You are an expert CV parser. Extract structured information from CVs into JSON format.
Be precise and extract only information that is explicitly stated in the CV."""
        
        user_prompt = f"""Parse the following CV and extract it into this JSON schema:

{{
  "personal_info": {{
    "name": "Full name",
    "title": "Professional title/headline",
    "email": "Email address",
    "phone": "Phone number",
    "linkedin": "LinkedIn URL",
    "github": "GitHub URL",
    "website": "Personal website",
    "location": "Location/City"
  }},
  "summary": "Professional summary/bio",
  "skills": {{
    "languages": ["Programming languages"],
    "frameworks": ["Frameworks and libraries"],
    "cloud": ["Cloud platforms and services"],
    "databases": ["Database technologies"],
    "tools": ["Development tools"],
    "other": ["Other technical skills"]
  }},
  "experience": [
    {{
      "title": "Job title",
      "company": "Company name",
      "location": "Location",
      "start_date": "Start date",
      "end_date": "End date or 'Present'",
      "achievements": ["Achievement 1", "Achievement 2"],
      "technologies": ["Tech used"]
    }}
  ],
  "education": [
    {{
      "degree": "Degree name",
      "institution": "University/School",
      "graduation_year": "Year",
      "gpa": "GPA if mentioned",
      "honors": ["Any honors/awards"]
    }}
  ],
  "projects": [
    {{
      "name": "Project name",
      "description": "Brief description",
      "technologies": ["Technologies used"],
      "url": "Project URL if available"
    }}
  ],
  "certifications": [
    {{
      "name": "Certification name",
      "issuer": "Issuing organization",
      "year": "Year obtained"
    }}
  ],
  "achievements": ["Notable achievements or awards"]
}}

If a field is not present in the CV, use null or an empty array as appropriate.

CV Text:
{cv_text}

Return ONLY valid JSON matching the schema above."""
        
        response = await self._query_llm(user_prompt, system_prompt)
        return json.loads(response)
    
    async def extract_job_json(self, jd_text: str) -> Dict[str, Any]:
        """Extract structured job posting data from text.
        
        Args:
            jd_text: Raw job description text
            
        Returns:
            Structured job data as dictionary
        """
        system_prompt = """You are an expert job posting parser. Extract structured information from job descriptions into JSON format.
Be precise and extract only information that is explicitly stated."""
        
        user_prompt = f"""Parse the following job description and extract it into this JSON schema:

{{
  "job_title": "Job title/role",
  "company": "Company name",
  "location": "Location (Remote/City/etc)",
  "employment_type": "Full-time/Part-time/Contract",
  "salary_range": "Salary range if mentioned",
  "experience_required": "Years of experience required",
  "overview": "Brief job overview/description",
  "responsibilities": [
    "Key responsibility 1",
    "Key responsibility 2"
  ],
  "required_qualifications": [
    "Required skill/qualification 1",
    "Required skill/qualification 2"
  ],
  "preferred_qualifications": [
    "Preferred skill 1",
    "Preferred skill 2"
  ],
  "technical_requirements": {{
    "languages": ["Required programming languages"],
    "frameworks": ["Required frameworks"],
    "cloud": ["Cloud platforms"],
    "databases": ["Database technologies"],
    "tools": ["Development tools"]
  }},
  "benefits": [
    "Benefit 1",
    "Benefit 2"
  ],
  "application_instructions": "How to apply",
  "company_culture": "Company culture description if mentioned"
}}

If a field is not present in the job description, use null or an empty array as appropriate.

Job Description:
{jd_text}

Return ONLY valid JSON matching the schema above."""
        
        response = await self._query_llm(user_prompt, system_prompt)
        return json.loads(response)
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


async def convert_cv_to_json(
    cv_source: str | Path,
    jd_source: str | Path | None = None,
    output_path: str | Path | None = None
) -> Dict[str, Any]:
    """Convert CV and optional job posting to JSON.
    
    Args:
        cv_source: Path or URL to CV
        jd_source: Optional path or URL to job description
        output_path: Optional path to save JSON output
        
    Returns:
        Dictionary with CV and optionally JD data
    """
    console.print("[bold blue]CV to JSON Converter[/bold blue]\n")
    
    result = {}
    
    # Load CV
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Loading CV...", total=None)
        
        try:
            cv_text, cv_type = ContentIngestor.load_content(cv_source)
            cv_text = ContentIngestor.clean_text(cv_text)
            console.print(f"[OK] CV loaded from {cv_type}: {len(cv_text)} characters")
        except Exception as e:
            console.print(f"[bold red]Error loading CV:[/bold red] {e}")
            raise
        
        progress.remove_task(task)
    
    # Load JD if provided
    jd_text = None
    if jd_source:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Loading job description...", total=None)
            
            try:
                jd_text, jd_type = ContentIngestor.load_content(jd_source)
                jd_text = ContentIngestor.clean_text(jd_text)
                console.print(f"[OK] Job description loaded from {jd_type}: {len(jd_text)} characters")
            except Exception as e:
                console.print(f"[bold yellow]Warning: Could not load JD:[/bold yellow] {e}")
            
            progress.remove_task(task)
    
    # Extract structured data
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Extracting structured data with AI...", total=None)
        
        async with CVToJSONConverter() as converter:
            # Extract CV data
            cv_data = await converter.extract_cv_json(cv_text)
            result["cv"] = cv_data
            console.print("[OK] CV data extracted")
            
            # Extract JD data if available
            if jd_text:
                jd_data = await converter.extract_job_json(jd_text)
                result["job_description"] = jd_data
                console.print("[OK] Job description data extracted")
        
        progress.remove_task(task)
    
    # Save to file if specified
    if output_path:
        output_file = Path(output_path)
        output_file.write_text(json.dumps(result, indent=2), encoding="utf-8")
        console.print(f"\n[bold green][OK] JSON saved to:[/bold green] {output_path}")
    
    # Display preview
    console.print("\n[bold cyan]Preview:[/bold cyan]")
    preview = json.dumps(result, indent=2)
    if len(preview) > 1000:
        console.print(preview[:1000] + "\n... (truncated)")
    else:
        console.print(preview)
    
    return result


def main_cv_to_json(
    cv: str,
    jd: str | None = None,
    output: str | None = None
) -> None:
    """Main entry point for CV to JSON conversion.
    
    Args:
        cv: Path or URL to CV
        jd: Optional path or URL to job description
        output: Optional output JSON file path
    """
    asyncio.run(convert_cv_to_json(cv, jd, output))


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        console.print("[bold red]Usage:[/bold red] python -m src.cv_to_json <cv_path_or_url> [jd_path_or_url] [output.json]")
        sys.exit(1)
    
    cv_arg = sys.argv[1]
    jd_arg = sys.argv[2] if len(sys.argv) > 2 else None
    output_arg = sys.argv[3] if len(sys.argv) > 3 else None
    
    main_cv_to_json(cv_arg, jd_arg, output_arg)
