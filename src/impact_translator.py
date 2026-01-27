"""Translate technical achievements into real-world impact explanations."""

from __future__ import annotations

from typing import Optional


class RealWorldImpactTranslator:
    """Translate technical jargon into non-technical, business-oriented impact statements."""

    # Mapping of technical terms to real-world impact translations
    IMPACT_TRANSLATIONS = {
        # Performance & Speed
        "optimized database query": "made the app faster for users",
        "improved performance": "made features respond quicker",
        "reduced latency": "decreased wait times",
        "improved caching": "reduced server load",
        "optimized algorithm": "improved efficiency",
        "increased throughput": "handled more requests",
        "faster execution": "quicker results for users",

        # Scale & Growth
        "scaled infrastructure": "supported growth from {X} to {Y} users",
        "handled traffic spike": "managed unexpected usage surge",
        "distributed system": "built system that could grow without breaking",
        "microservices": "modular system allowing independent scaling",
        "horizontal scaling": "added capacity by adding more servers",

        # Reliability & Quality
        "improved uptime": "reduced downtime and service interruptions",
        "fault tolerance": "system keeps working even when parts fail",
        "redundancy": "ensured service didn't go down",
        "monitoring system": "got alerts before users noticed problems",
        "automated testing": "caught bugs before they reached users",
        "ci/cd pipeline": "deployed changes faster and more safely",

        # Data & Analytics
        "data pipeline": "automated data collection and reporting",
        "business intelligence": "helped teams make data-driven decisions",
        "analytics dashboard": "gave stakeholders visibility into metrics",
        "machine learning model": "automated decision-making process",
        "predictive analytics": "forecasted trends and behaviors",
        "data warehouse": "centralized data for company-wide insights",

        # User Experience
        "improved ui/ux": "made the product easier to use",
        "mobile optimization": "ensured app worked well on phones",
        "accessibility features": "enabled people with disabilities to use the product",
        "redesigned interface": "made navigation more intuitive",
        "simplified workflow": "reduced steps needed to complete tasks",

        # Backend & Architecture
        "refactored codebase": "made code easier to maintain and change",
        "modular design": "reduced dependencies and silo effects",
        "api integration": "connected systems that didn't talk before",
        "database optimization": "improved data query speeds",
        "load balancing": "distributed traffic evenly across servers",

        # Security & Compliance
        "security audit": "identified and fixed vulnerabilities",
        "encryption implementation": "protected sensitive data",
        "compliance framework": "met regulatory requirements",
        "access controls": "ensured only authorized people saw sensitive data",

        # Cost & Efficiency
        "cost reduction": "saved company money on infrastructure",
        "resource optimization": "reduced wasted computational resources",
        "serverless architecture": "paid only for what we used",
        "cloud migration": "reduced on-premise hardware costs",
    }

    @classmethod
    def translate_bullet(cls, technical_bullet: str) -> str:
        """Translate a technical bullet point into non-technical impact.
        
        Args:
            technical_bullet: A technical achievement bullet
            
        Returns:
            Non-technical impact explanation (or original if no translation found)
        """
        bullet_lower = technical_bullet.lower()

        # Check for direct matches
        for technical_term, impact_phrase in cls.IMPACT_TRANSLATIONS.items():
            if technical_term in bullet_lower:
                # Extract any metrics from original bullet
                metrics = cls._extract_metrics(technical_bullet)
                if metrics:
                    return f"{impact_phrase} ({metrics})"
                return impact_phrase

        # No direct match - try to add context
        return cls._enhance_with_context(technical_bullet)

    @classmethod
    def _extract_metrics(cls, bullet: str) -> Optional[str]:
        """Extract quantifiable metrics from a bullet point.
        
        Args:
            bullet: Technical bullet text
            
        Returns:
            Extracted metrics or None
        """
        import re

        # Look for percentages, numbers with units, time-based metrics
        patterns = [
            r"(\d+%)",  # Percentage
            r"(\d+\.?\d*\s*(?:x|times)?)",  # Multiplier
            r"(\d+\s*(?:seconds?|minutes?|hours?|days?|months?|years?))",  # Time
            r"(\d+(?:K|M|B|,\d+)(?:\s*(?:users?|requests?|transactions?)))",  # Volume
        ]

        for pattern in patterns:
            match = re.search(pattern, bullet, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    @classmethod
    def _enhance_with_context(cls, technical_bullet: str) -> str:
        """Try to infer impact from keyword presence.
        
        Args:
            technical_bullet: Technical bullet
            
        Returns:
            Enhanced bullet with implied impact
        """
        keywords_impact = {
            ("built", "developed", "created", "engineered"): "delivered feature",
            ("reduced", "minimized", "decreased", "lowered"): "improved",
            ("increased", "improved", "enhanced", "optimized"): "strengthened",
            ("automated", "orchestrated", "streamlined"): "made more efficient",
            ("redesigned", "refactored", "restructured"): "improved maintainability",
        }

        bullet_lower = technical_bullet.lower()

        for keywords, impact_verb in keywords_impact.items():
            if any(kw in bullet_lower for kw in keywords):
                return f"{impact_verb.capitalize()} {technical_bullet.lower()}"

        # Fallback: just capitalize and return
        return technical_bullet

    @classmethod
    def add_business_impact(cls, achievement: str, optional_context: str = "") -> str:
        """Add business impact context to an achievement.
        
        Args:
            achievement: The technical achievement
            optional_context: Optional context (e.g., "50K daily users", "finance team")
            
        Returns:
            Achievement with business impact context
        """
        # Get base impact
        impact = cls.translate_bullet(achievement)

        # Add context if provided
        if optional_context:
            return f"{impact} benefiting {optional_context}"

        return impact

    @classmethod
    def translate_section_bullets(cls, bullets: list[str]) -> list[str]:
        """Translate a list of bullets to include business impact.
        
        Args:
            bullets: List of technical bullet points
            
        Returns:
            List of bullets with real-world impact language
        """
        return [cls.translate_bullet(bullet) for bullet in bullets]
