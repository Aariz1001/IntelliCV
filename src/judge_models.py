"""Pydantic models for the CV Judge ensemble system."""

from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field


class ModelEvaluation(BaseModel):
    """Evaluation from a single AI model judge."""
    
    score: int = Field(ge=0, le=100, description="Overall match score from 0-100")
    matching_skills: List[str] = Field(default_factory=list, description="Skills that match the JD requirements")
    missing_requirements: List[str] = Field(default_factory=list, description="JD requirements not found in CV")
    red_flags: List[str] = Field(default_factory=list, description="Potential concerns or issues")
    strengths: List[str] = Field(default_factory=list, description="Key strengths of the candidate")
    rationale: str = Field(description="Detailed reasoning for the score")
    model_name: str = Field(description="Name of the model that generated this evaluation")


class FinalReport(BaseModel):
    """Aggregated report from all model judges."""
    
    consensus_score: float = Field(description="Weighted average score from all models")
    judge_discordance: bool = Field(
        default=False,
        description="True if scores vary by more than 25 points"
    )
    detailed_breakdown: Dict[str, ModelEvaluation] = Field(
        default_factory=dict,
        description="Individual evaluations from each model"
    )
    consensus_highlights: List[str] = Field(
        default_factory=list,
        description="Points where all models agree"
    )
    discordance_points: List[str] = Field(
        default_factory=list,
        description="Points where models significantly disagree"
    )
    recommendation: str = Field(
        description="Final hiring recommendation based on ensemble analysis"
    )


class AnalysisContext(BaseModel):
    """Context for CV analysis including source documents."""
    
    cv_text: str = Field(description="Full text of the candidate's CV")
    jd_text: str = Field(description="Full text of the job description")
    guidance: str | None = Field(default=None, description="Optional user guidance for evaluation")
