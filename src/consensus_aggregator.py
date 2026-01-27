"""Consensus aggregator for combining multiple AI judge evaluations."""

from __future__ import annotations

from typing import Dict, List, Set

from .judge_models import FinalReport, ModelEvaluation
from .judge_orchestrator import JudgeOrchestrator


class ConsensusAggregator:
    """Aggregates evaluations from multiple AI models into a consensus report."""
    
    DISCORDANCE_THRESHOLD = 25  # Score variance threshold to flag discordance
    
    @staticmethod
    def calculate_consensus_score(
        evaluations: Dict[str, ModelEvaluation],
        weights: Dict[str, float] | None = None
    ) -> float:
        """Calculate weighted average score from multiple evaluations.
        
        Args:
            evaluations: Dictionary of model evaluations
            weights: Optional custom weights (defaults to orchestrator weights)
            
        Returns:
            Weighted average score
        """
        if not evaluations:
            return 0.0
        
        # Use orchestrator weights if not provided
        if weights is None:
            weights = {
                key: JudgeOrchestrator.MODELS[key]["weight"]
                for key in JudgeOrchestrator.MODELS.keys()
            }
        
        total_weight = 0.0
        weighted_sum = 0.0
        
        for model_key, evaluation in evaluations.items():
            weight = weights.get(model_key, 1.0 / len(evaluations))
            weighted_sum += evaluation.score * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    @staticmethod
    def detect_discordance(evaluations: Dict[str, ModelEvaluation]) -> bool:
        """Check if model scores vary beyond the threshold.
        
        Args:
            evaluations: Dictionary of model evaluations
            
        Returns:
            True if discordance detected
        """
        if len(evaluations) < 2:
            return False
        
        scores = [e.score for e in evaluations.values()]
        score_range = max(scores) - min(scores)
        
        return score_range > ConsensusAggregator.DISCORDANCE_THRESHOLD
    
    @staticmethod
    def find_consensus_highlights(evaluations: Dict[str, ModelEvaluation]) -> List[str]:
        """Find points where all models agree.
        
        Args:
            evaluations: Dictionary of model evaluations
            
        Returns:
            List of consensus highlights
        """
        if not evaluations:
            return []
        
        # Find skills mentioned by all models
        all_skills: List[Set[str]] = [
            set(e.matching_skills) for e in evaluations.values()
        ]
        common_skills = set.intersection(*all_skills) if all_skills else set()
        
        # Find red flags mentioned by all models
        all_red_flags: List[Set[str]] = [
            set(e.red_flags) for e in evaluations.values()
        ]
        common_red_flags = set.intersection(*all_red_flags) if all_red_flags else set()
        
        highlights = []
        
        if common_skills:
            highlights.append(
                f"Universally recognized skills: {', '.join(sorted(common_skills))}"
            )
        
        if common_red_flags:
            highlights.append(
                f"Unanimous concerns: {', '.join(sorted(common_red_flags))}"
            )
        
        # Check if all models agree on score range
        scores = [e.score for e in evaluations.values()]
        if max(scores) - min(scores) <= 10:
            avg_score = sum(scores) / len(scores)
            if avg_score >= 80:
                highlights.append("All models strongly recommend this candidate")
            elif avg_score <= 40:
                highlights.append("All models have significant concerns about fit")
            else:
                highlights.append(f"All models agree on moderate fit (score variance < 10)")
        
        return highlights
    
    @staticmethod
    def find_discordance_points(evaluations: Dict[str, ModelEvaluation]) -> List[str]:
        """Find points where models significantly disagree.
        
        Args:
            evaluations: Dictionary of model evaluations
            
        Returns:
            List of discordance points
        """
        if len(evaluations) < 2:
            return []
        
        discordance = []
        
        # Check score variance
        scores = {k: e.score for k, e in evaluations.items()}
        if max(scores.values()) - min(scores.values()) > ConsensusAggregator.DISCORDANCE_THRESHOLD:
            high_scorer = max(scores, key=scores.get)
            low_scorer = min(scores, key=scores.get)
            discordance.append(
                f"Score disagreement: {JudgeOrchestrator.MODELS[high_scorer]['name']} "
                f"rated {scores[high_scorer]}, while {JudgeOrchestrator.MODELS[low_scorer]['name']} "
                f"rated {scores[low_scorer]}"
            )
        
        # Find skills mentioned by some but not all
        all_skills: Dict[str, Set[str]] = {
            k: set(e.matching_skills) for k, e in evaluations.items()
        }
        
        for model_key, skills in all_skills.items():
            unique_skills = skills - set.union(*[s for k, s in all_skills.items() if k != model_key])
            if unique_skills:
                discordance.append(
                    f"{JudgeOrchestrator.MODELS[model_key]['name']} uniquely identified: "
                    f"{', '.join(sorted(unique_skills))}"
                )
        
        return discordance
    
    @staticmethod
    def generate_recommendation(
        consensus_score: float,
        judge_discordance: bool,
        evaluations: Dict[str, ModelEvaluation]
    ) -> str:
        """Generate a final hiring recommendation.
        
        Args:
            consensus_score: The aggregated score
            judge_discordance: Whether models disagree significantly
            evaluations: Individual model evaluations
            
        Returns:
            Recommendation text
        """
        if judge_discordance:
            return (
                f"[!] **Manual Review Required** - Models show significant disagreement. "
                f"Consensus score: {consensus_score:.1f}. "
                f"Recommend human review to resolve discrepancies."
            )
        
        if consensus_score >= 80:
            return (
                f"[OK] **Strong Recommend** - Excellent match with consensus score of {consensus_score:.1f}. "
                f"Candidate demonstrates strong alignment with job requirements."
            )
        elif consensus_score >= 65:
            return (
                f"👍 **Recommend** - Good match with consensus score of {consensus_score:.1f}. "
                f"Candidate meets most key requirements with some areas for growth."
            )
        elif consensus_score >= 50:
            return (
                f"🤔 **Consider with Caution** - Moderate match with consensus score of {consensus_score:.1f}. "
                f"Candidate has potential but significant gaps exist."
            )
        else:
            return (
                f"[X] **Not Recommended** - Weak match with consensus score of {consensus_score:.1f}. "
                f"Candidate does not meet core job requirements."
            )
    
    @staticmethod
    def aggregate(evaluations: Dict[str, ModelEvaluation]) -> FinalReport:
        """Aggregate multiple evaluations into a final consensus report.
        
        Args:
            evaluations: Dictionary mapping model keys to evaluations
            
        Returns:
            Final aggregated report
        """
        consensus_score = ConsensusAggregator.calculate_consensus_score(evaluations)
        judge_discordance = ConsensusAggregator.detect_discordance(evaluations)
        consensus_highlights = ConsensusAggregator.find_consensus_highlights(evaluations)
        discordance_points = ConsensusAggregator.find_discordance_points(evaluations)
        recommendation = ConsensusAggregator.generate_recommendation(
            consensus_score,
            judge_discordance,
            evaluations
        )
        
        return FinalReport(
            consensus_score=round(consensus_score, 1),
            judge_discordance=judge_discordance,
            detailed_breakdown=evaluations,
            consensus_highlights=consensus_highlights,
            discordance_points=discordance_points,
            recommendation=recommendation
        )
