"""Judge orchestrator for managing ensemble AI evaluations via OpenRouter."""

from __future__ import annotations

import asyncio
import json
import os
from typing import Dict, List

import httpx
from pydantic import ValidationError

from .judge_models import AnalysisContext, ModelEvaluation


class JudgeOrchestrator:
    """Orchestrates parallel CV evaluations across multiple AI models."""
    
    # Model configurations
    MODELS = {
        "gemini": {
            "id": "google/gemini-3-flash-preview",
            "name": "Gemini 3 Flash Preview",
            "role": "Reasoning Lead",
            "weight": 0.35
        },
        "kimi": {
            "id": "moonshotai/kimi-k2-0905",
            "name": "Kimi K2",
            "role": "Analytical",
            "weight": 0.35
        },
        "glm": {
            "id": "z-ai/glm-4.7",
            "name": "GLM-4.7",
            "role": "Validation",
            "weight": 0.30
        }
    }
    
    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    def __init__(self, api_key: str | None = None):
        """Initialize the orchestrator.
        
        Args:
            api_key: OpenRouter API key. If not provided, will look for OPENROUTER_API_KEY env var
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key required. Set OPENROUTER_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0),
            limits=httpx.Limits(max_connections=10)
        )
    
    def _build_system_prompt(self, context: AnalysisContext) -> str:
        """Build the system prompt for AI judges.
        
        Args:
            context: Analysis context with CV, JD, and guidance
            
        Returns:
            Formatted system prompt
        """
        guidance_section = ""
        if context.guidance:
            guidance_section = f"\n\n**Special Guidance:** {context.guidance}"
        
        return f"""You are an expert technical recruiter evaluating a candidate's CV against a job description.

Your task is to provide a structured, evidence-based evaluation using a Chain-of-Thought approach:

1. Extract 3-5 key requirements from the job description
2. For each requirement, search for verbatim evidence in the CV
3. Identify matching skills and missing requirements
4. Note any red flags or concerns
5. Highlight the candidate's key strengths
6. Provide an overall match score (0-100) with detailed rationale

Be specific and cite evidence directly from the documents. Do not hallucinate qualifications.{guidance_section}

**Job Description:**
{context.jd_text}

**Candidate CV:**
{context.cv_text}

Respond with a valid JSON object matching this schema:
{{
    "score": <integer 0-100>,
    "matching_skills": [<list of skills that match>],
    "missing_requirements": [<list of JD requirements not in CV>],
    "red_flags": [<list of concerns>],
    "strengths": [<list of key strengths>],
    "rationale": "<detailed reasoning for the score>",
    "model_name": "<your model name>"
}}"""
    
    async def _query_model(
        self,
        model_key: str,
        context: AnalysisContext,
        max_retries: int = 3
    ) -> ModelEvaluation | None:
        """Query a single AI model with retry logic.
        
        Args:
            model_key: Key identifying the model in MODELS dict
            context: Analysis context
            max_retries: Maximum number of retry attempts
            
        Returns:
            ModelEvaluation or None if all retries failed
        """
        model_config = self.MODELS[model_key]
        system_prompt = self._build_system_prompt(context)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model_config["id"],
            "messages": [
                {"role": "user", "content": system_prompt}
            ],
            "temperature": 0.3,
            "response_format": {"type": "json_object"}
        }
        
        for attempt in range(max_retries):
            try:
                response = await self.client.post(
                    self.BASE_URL,
                    json=payload,
                    headers=headers
                )
                
                # Handle rate limiting
                if response.status_code == 429:
                    wait_time = 2 ** attempt  # Exponential backoff
                    await asyncio.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                # Extract the response content
                content = data["choices"][0]["message"]["content"]
                evaluation_data = json.loads(content)
                
                # Ensure model_name is set
                evaluation_data["model_name"] = model_config["name"]
                
                # Validate and return
                return ModelEvaluation(**evaluation_data)
                
            except (httpx.HTTPError, json.JSONDecodeError, ValidationError, KeyError) as e:
                print(f"Attempt {attempt + 1}/{max_retries} failed for {model_config['name']}: {e}")
                if attempt == max_retries - 1:
                    return None
                await asyncio.sleep(1)
        
        return None
    
    async def run_ensemble(self, context: AnalysisContext) -> Dict[str, ModelEvaluation]:
        """Run the ensemble evaluation across all models in parallel.
        
        Args:
            context: Analysis context with CV, JD, and optional guidance
            
        Returns:
            Dictionary mapping model keys to their evaluations
        """
        tasks = [
            self._query_model(model_key, context)
            for model_key in self.MODELS.keys()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        evaluations = {}
        for model_key, result in zip(self.MODELS.keys(), results):
            if isinstance(result, ModelEvaluation):
                evaluations[model_key] = result
            else:
                print(f"Warning: {self.MODELS[model_key]['name']} failed to produce evaluation")
        
        return evaluations
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
