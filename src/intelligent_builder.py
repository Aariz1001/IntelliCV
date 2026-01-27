"""Integrated CV optimization pipeline with config-driven intelligence."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Any
import json
import re
import logging

from .cv_config import CVConfig
from .config_parser import load_config_from_file, create_default_config
from .docx_analyzer import DocxAnalyzer
from .content_optimizer import ContentOptimizer
from .change_tracker import ChangeReport, Change, ChangeType
from .review_system import ReviewSystem
from .impact_translator import RealWorldImpactTranslator
from .utils import load_json, save_json
from .config import load_config

logger = logging.getLogger(__name__)



class IntelligentCVBuilder:
    """Main pipeline for intelligent CV optimization with config support."""

    def __init__(
        self,
        cv_json: dict[str, Any],
        config: CVConfig,
        changes_dir: str | Path = "changes",
    ):
        """Initialize the builder.
        
        Args:
            cv_json: Input CV as dictionary
            config: CVConfig with optimization settings
            changes_dir: Directory for saving change reports
        """
        self.cv_json = cv_json
        self.config = config
        self.optimizer = ContentOptimizer(config)
        self.review_system = ReviewSystem(changes_dir)
        self.original_cv = self._deep_copy(cv_json)

    def optimize_for_page_limit(
        self,
        current_pages: Optional[int] = None,
        interactive: bool = False,
    ) -> tuple[dict[str, Any], ChangeReport]:
        """Optimize CV content to fit page limit.
        
        Args:
            current_pages: Current page count (auto-detect if None)
            interactive: If True, prompt user to review changes
            
        Returns:
            Tuple of (optimized_cv, change_report)
        """
        # Estimate current page count if not provided
        if current_pages is None:
            # Would need existing DOCX to analyze
            current_pages = 2  # Default estimate

        target_pages = self.config.page_limit

        # If already under page limit, just return with no changes
        if current_pages <= target_pages:
            report = self.optimizer.get_change_report()
            return self.cv_json, report

        print(f"\n[CV Optimization]")
        print(f"   Current: ~{current_pages} pages")
        print(f"   Target: {target_pages} page(s)")

        # Estimate words to remove
        # Rough heuristic: 275 words per page
        words_per_page = 275
        words_to_remove = (current_pages - target_pages) * words_per_page

        # Phase 1: Remove items by priority
        optimized_cv = self.optimizer.remove_sections_by_priority(
            self.cv_json,
            int(words_to_remove * 0.7),  # Remove 70% via item removal
        )

        # Phase 2: Condense remaining bullets
        for section in ["experience", "projects", "skills"]:
            optimized_cv = self.optimizer.condense_bullets_in_section(
                optimized_cv,
                section,
                target_reduction=0.2,
            )

        # Phase 3: Add real-world impact to remaining content
        optimized_cv = self._add_impact_statements(optimized_cv)

        report = self.optimizer.get_change_report()

        # Interactive review if requested
        if interactive:
            optimized_cv = self._interactive_review(optimized_cv, report)

        return optimized_cv, report

    def _add_impact_statements(self, cv_json: dict[str, Any]) -> dict[str, Any]:
        """Add real-world impact language to CV content.
        
        Args:
            cv_json: CV dictionary
            
        Returns:
            CV with enhanced impact statements
        """
        modified_cv = self._deep_copy(cv_json)

        # Enhance bullets with business impact language
        for section in ["experience", "projects"]:
            items = modified_cv.get(section, [])
            if not isinstance(items, list):
                continue

            for item in items:
                if "bullets" in item and isinstance(item["bullets"], list):
                    # Translate bullets to include real-world impact
                    enhanced_bullets = []
                    for bullet in item["bullets"]:
                        # Add impact context if not already present
                        if not self._has_business_impact_language(bullet):
                            enhanced = RealWorldImpactTranslator.translate_bullet(bullet)
                            enhanced_bullets.append(enhanced)
                        else:
                            enhanced_bullets.append(bullet)
                    item["bullets"] = enhanced_bullets

        return modified_cv

    def _has_business_impact_language(self, bullet: str) -> bool:
        """Check if bullet already has business impact language.
        
        Args:
            bullet: Bullet text
            
        Returns:
            True if bullet already mentions impact
        """
        impact_keywords = {
            "increased", "improved", "reduced", "accelerated", "enabled",
            "saved", "generated", "delivered", "achieved", "%", " users", " million"
        }
        bullet_lower = bullet.lower()
        return any(keyword in bullet_lower for keyword in impact_keywords)

    def tailor_with_ai(
        self,
        readmes: Optional[dict[str, str]] = None,
        guidance: Optional[str] = None,
    ) -> tuple[dict[str, Any], ChangeReport]:
        """Apply AI-powered tailoring for hiring-manager focus and GitHub context.
        
        Args:
            readmes: Dictionary of GitHub README files
            guidance: Optional custom tailoring guidance
            
        Returns:
            Tuple of (tailored_cv, change_report)
        """
        import requests
        
        # Load OpenRouter config
        api_config = load_config()
        
        print(f"\n[AI Tailoring with GitHub Context]")
        if readmes:
            print(f"   Integrating {len(readmes)} GitHub README(s)")
        if guidance:
            print(f"   Custom guidance: {guidance[:60]}...")
        
        # Build prompt with inventory
        prompt = self._build_ai_prompt(self.cv_json, readmes or {}, guidance)
        
        # Call OpenRouter API
        print("   Sending to AI for optimization...")
        
        headers = {
            "Authorization": f"Bearer {api_config.openrouter.api_key}",
            "Content-Type": "application/json",
        }
        if api_config.openrouter.http_referer:
            headers["HTTP-Referer"] = api_config.openrouter.http_referer
        if api_config.openrouter.x_title:
            headers["X-Title"] = api_config.openrouter.x_title
        
        payload = {
            "model": api_config.openrouter.model,
            "messages": [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt},
            ],
            "temperature": 1.0,
            "reasoning": {"effort": api_config.openrouter.reasoning_effort},
        }
        
        response = requests.post(
            f"{api_config.openrouter.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=300,
        )
        
        if not response.ok:
            raise ValueError(f"OpenRouter error: {response.status_code} {response.text}")
        
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        tailored_cv = self._extract_json(content)
        
        # CRITICAL: Fix capitalized keys and normalize schema
        # AI might return "Name", "Summary" etc - we need lowercase
        tailored_cv = self._normalize_schema(tailored_cv)
        
        # CRITICAL: Validate preservation - prevent unwanted rewrites
        tailored_cv = self._validate_preservation(self.original_cv, tailored_cv)
        
        # CRITICAL: Preserve required fields from original CV
        # The AI might not preserve these, so we ensure they're there
        required_fields = {
            "name": self.original_cv.get("name", ""),
            "title": self.original_cv.get("title", ""),
            "contact": self.original_cv.get("contact", {}),
            "summary": self.original_cv.get("summary", []),  # MUST preserve summary!
        }
        
        for field, default_value in required_fields.items():
            if field not in tailored_cv or not tailored_cv.get(field):
                tailored_cv[field] = default_value
        
        # Create change report (comparing original to tailored)
        report = self._compare_and_report(self.original_cv, tailored_cv, "AI Tailoring")
        
        print("   [OK] AI tailoring complete")
        return tailored_cv, report

    def optimize_and_tailor(
        self,
        readmes: Optional[dict[str, str]] = None,
        guidance: Optional[str] = None,
        interactive: bool = False,
    ) -> tuple[dict[str, Any], ChangeReport]:
        """Combined optimization and AI tailoring - best of both worlds!
        
        Args:
            readmes: Dictionary of GitHub README files
            guidance: Optional custom tailoring guidance
            interactive: If True, prompt user to review changes
            
        Returns:
            Tuple of (optimized_and_tailored_cv, combined_change_report)
        """
        print("\n[INTELLIGENT CV ENHANCEMENT] (Optimize + AI Tailor)")
        
        # Phase 1: Content Optimization
        print("\n[Phase 1] Optimize for page fit...")
        optimized_cv, opt_report = self.optimize_for_page_limit(interactive=False)
        
        # Phase 2: AI Tailoring
        print("\n[Phase 2] AI tailoring with GitHub context...")
        self.cv_json = optimized_cv  # Update for next phase
        tailored_cv, tailor_report = self.tailor_with_ai(readmes, guidance)
        
        # Phase 3: Interactive review (if requested)
        if interactive:
            print("\n[Phase 3] Interactive review...")
            tailored_cv = self._interactive_review(tailored_cv, tailor_report)
        
        # Combine reports
        combined_report = ChangeReport()
        combined_report.changes = opt_report.changes + tailor_report.changes
        
        return tailored_cv, combined_report

    def _build_ai_prompt(
        self,
        cv_json: dict,
        readmes: dict[str, str],
        guidance: Optional[str],
    ) -> str:
        """Build comprehensive prompt for AI tailoring.
        
        Args:
            cv_json: CV data
            readmes: GitHub READMEs
            guidance: Custom guidance
            
        Returns:
            Prompt string
        """
        inventory = self._build_cv_inventory(cv_json)
        
        prompt = f"""Please optimize and enhance this CV for maximum hiring-manager impact:

{inventory}

"""
        
        if readmes:
            prompt += "GitHub Projects Context:\n"
            for filename, content in readmes.items():
                # Extract first 500 chars of README for context
                summary = content[:500].replace("\n", " ")
                prompt += f"- {filename}: {summary}...\n"
            prompt += "\n"
        
        prompt += """Task:
1. Rewrite bullets to be impact-first (biggest wins first)
2. Add metrics and quantified results wherever possible
3. Use action verbs (Built, Designed, Implemented, etc)
4. Integrate GitHub project context to prove credibility
5. Fit content onto ONE PAGE through better writing (not deletion)
6. Keep ALL original achievements - just rewrite them better

Return ONLY valid JSON matching the input CV schema."""
        
        if guidance:
            prompt += f"\n\nAdditional guidance from user:\n{guidance}"
        
        return prompt

    def _build_cv_inventory(self, cv_json: dict) -> str:
        """Create structured inventory of CV contents."""
        name = (cv_json.get("name") or "").strip()
        title = (cv_json.get("title") or "").strip()
        summary = cv_json.get("summary", []) or []
        experience = cv_json.get("experience", []) or []
        projects = cv_json.get("projects", []) or []
        education = cv_json.get("education", []) or []
        
        lines = [
            f"Name: {name or '(missing)'}",
            f"Title: {title or '(missing)'}",
            f"Summary: {len(summary)} points",
            f"Experience: {len(experience)} roles",
            f"Projects: {len(projects)} items",
            f"Education: {len(education)} entries",
        ]
        
        if experience:
            lines.append("\nExperience:")
            for item in experience:
                role = item.get("role", "")
                company = item.get("company", "")
                bullets = len(item.get("bullets", []))
                lines.append(f"  - {role} at {company} ({bullets} bullets)")
        
        if projects:
            lines.append("\nProjects:")
            for item in projects:
                name = item.get("name", "")
                bullets = len(item.get("bullets", []))
                lines.append(f"  - {name} ({bullets} bullets)")
        
        return "\n".join(lines)

    def _get_system_prompt(self) -> str:
        """Get AI system prompt for world-class CV writing."""
        return """You are a world-class technical resume writer and career coach who has helped thousands of engineers land jobs at top tech companies (FAANG, startups, Fortune 500).

Your expertise includes:
- ATS (Applicant Tracking System) optimization
- Quantified impact statements with metrics
- Action-verb-first bullet points
- Keyword density for technical roles
- Concise, high-impact writing

CRITICAL JSON SCHEMA REQUIREMENTS:
Return ONLY valid JSON with EXACTLY these lowercase keys:
- name (string): Full name
- title (string): Professional title
- summary (array of strings): Key achievements/overview
- contact (object): {email, phone, location, links}
- experience (array of objects): {company, role, dates, location, bullets}
- projects (array of objects): {name, link, dates, bullets}
- education (array of objects): {school, degree, dates, location, details}
- skills (object): {groups: array of {name, items}}
- certifications (array)
- awards (array)

ABSOLUTE RULES (CRITICAL - DO NOT VIOLATE):
1. Return ONLY valid JSON with lowercase keys EXACTLY as listed above.
2. No markdown, commentary, or extra keys.
3. **PRESERVE 100% OF ORIGINAL CONTENT** - only light tightening and wording improvements.
4. **DO NOT rewrite or change the meaning** of existing sections (summary, projects, experience, education).
5. **DO NOT delete or remove** any original bullets, projects, or achievements.
6. **DO NOT replace** existing projects - they stay exactly as provided.
7. **DO NOT replace** the summary - only minor wording improvements if needed.
8. **DO NOT change field names** or add new fields beyond what was in the input.
9. Keep all original capitalization, structure, and content order.
10. Edits allowed ONLY: 
    - Tighten passive voice to active (rare)
    - Fix obvious typos
    - Add missing action verbs to bullets (without changing meaning)
    - Condense redundant phrasing (max 10-15% shorter)
11. Every bullet MUST start with a strong action verb.
12. Include specific numbers, percentages, and metrics wherever possible.
13. If you cannot parse the input, return it unchanged.
14. When in doubt, preserve the original."""

    def _validate_preservation(self, original: dict, modified: dict) -> dict:
        """Validate that critical sections weren't rewritten - restore if needed.
        
        This prevents the AI from replacing entire sections when it should only
        be tightening or enhancing with GitHub context.
        """
        preserved = modified.copy()
        
        # Rule 1: Summary should NOT be completely replaced
        # If original summary exists and modified is very different, restore it
        if "summary" in original and original["summary"]:
            original_summary = original.get("summary", [])
            modified_summary = modified.get("summary", [])
            
            # If summary is completely different (< 30% overlap), restore original
            if original_summary and modified_summary:
                original_set = set(original_summary)
                modified_set = set(modified_summary)
                overlap = len(original_set & modified_set) / len(original_set) if original_set else 0
                
                if overlap < 0.3:  # Less than 30% of original preserved
                    logger.warning(f"Summary was rewritten (only {overlap*100:.0f}% preserved), restoring original")
                    preserved["summary"] = original_summary
        
        # Rule 2: Projects should NOT be deleted
        # Keep original projects, optionally add GitHub projects as new ones
        if "projects" in original:
            original_projects = original.get("projects", [])
            modified_projects = modified.get("projects", [])
            
            # Extract original project names for comparison
            original_names = {p.get("name", "").lower() for p in original_projects}
            modified_names = {p.get("name", "").lower() for p in modified_projects}
            
            # If more than 50% of projects were deleted, restore original
            missing_count = len(original_names - modified_names)
            if missing_count / len(original_names) > 0.5 if original_names else False:
                logger.warning(f"{missing_count} original projects were deleted, restoring all")
                preserved["projects"] = original_projects
        
        # Rule 3: Experience should NOT be replaced
        if "experience" in original:
            original_exp = original.get("experience", [])
            modified_exp = modified.get("experience", [])
            
            # If experience is empty or much shorter, restore
            if not modified_exp and original_exp:
                logger.warning("Experience was deleted, restoring original")
                preserved["experience"] = original_exp
        
        # Rule 4: Education should NOT be deleted
        if "education" in original:
            original_edu = original.get("education", [])
            modified_edu = modified.get("education", [])
            
            if not modified_edu and original_edu:
                logger.warning("Education was deleted, restoring original")
                preserved["education"] = original_edu
        
        # Rule 5: Skills should NOT be deleted
        if "skills" in original:
            original_skills = original.get("skills", {})
            modified_skills = modified.get("skills", {})
            
            if not modified_skills and original_skills:
                logger.warning("Skills were deleted, restoring original")
                preserved["skills"] = original_skills
        
        return preserved

    def _normalize_schema(self, cv_json: dict[str, Any]) -> dict[str, Any]:
        """Normalize CV JSON schema - fix capitalized keys and ensure required fields."""
        normalized = {}
        
        # Map of possible key variations to canonical lowercase keys
        key_mapping = {
            'name': ['Name', 'NAME'],
            'title': ['Title', 'TITLE'],
            'summary': ['Summary', 'SUMMARY'],
            'contact': ['Contact', 'CONTACT'],
            'experience': ['Experience', 'EXPERIENCE'],
            'projects': ['Projects', 'PROJECTS'],
            'education': ['Education', 'EDUCATION'],
            'skills': ['Skills', 'SKILLS'],
            'certifications': ['Certifications', 'CERTIFICATIONS'],
            'awards': ['Awards', 'AWARDS'],
        }
        
        # Nested key mappings for experience, projects, education items
        experience_key_mapping = {
            'company': ['Company', 'COMPANY'],
            'role': ['Role', 'ROLE', 'Title', 'Position'],
            'location': ['Location', 'LOCATION'],
            'dates': ['Dates', 'DATES', 'Date', 'Period'],
            'bullets': ['Bullets', 'BULLETS', 'Points', 'Achievements'],
        }
        
        project_key_mapping = {
            'name': ['Name', 'NAME', 'Title'],
            'link': ['Link', 'LINK', 'URL', 'Url'],
            'dates': ['Dates', 'DATES', 'Date'],
            'bullets': ['Bullets', 'BULLETS', 'Points', 'Description'],
        }
        
        education_key_mapping = {
            'school': ['School', 'SCHOOL', 'Institution', 'University'],
            'degree': ['Degree', 'DEGREE'],
            'location': ['Location', 'LOCATION'],
            'dates': ['Dates', 'DATES', 'Date'],
            'details': ['Details', 'DETAILS', 'Bullets'],
        }
        
        def normalize_nested(item: dict, mapping: dict) -> dict:
            """Normalize keys in a nested object."""
            result = {}
            for canonical, variations in mapping.items():
                if canonical in item:
                    result[canonical] = item[canonical]
                else:
                    for variation in variations:
                        if variation in item:
                            result[canonical] = item[variation]
                            break
            return result
        
        # Normalize each top-level field
        for canonical, variations in key_mapping.items():
            # Check if canonical exists
            if canonical in cv_json:
                normalized[canonical] = cv_json[canonical]
            else:
                # Check variations
                found = False
                for variation in variations:
                    if variation in cv_json:
                        normalized[canonical] = cv_json[variation]
                        found = True
                        break
                
                # If not found, use default
                if not found:
                    if canonical == 'name':
                        normalized[canonical] = ''
                    elif canonical == 'title':
                        normalized[canonical] = ''
                    elif canonical == 'summary':
                        normalized[canonical] = []
                    elif canonical == 'contact':
                        normalized[canonical] = {'email': '', 'phone': '', 'location': '', 'links': []}
                    elif canonical in ['experience', 'projects', 'education']:
                        normalized[canonical] = []
                    elif canonical == 'skills':
                        normalized[canonical] = {'groups': []}
                    elif canonical in ['certifications', 'awards']:
                        normalized[canonical] = []
        
        # Normalize nested experience items
        if 'experience' in normalized and isinstance(normalized['experience'], list):
            normalized['experience'] = [
                normalize_nested(exp, experience_key_mapping) if isinstance(exp, dict) else exp
                for exp in normalized['experience']
            ]
        
        # Normalize nested project items
        if 'projects' in normalized and isinstance(normalized['projects'], list):
            normalized['projects'] = [
                normalize_nested(proj, project_key_mapping) if isinstance(proj, dict) else proj
                for proj in normalized['projects']
            ]
        
        # Normalize nested education items
        if 'education' in normalized and isinstance(normalized['education'], list):
            new_edu = []
            for edu in normalized['education']:
                if isinstance(edu, dict):
                    new_edu.append(normalize_nested(edu, education_key_mapping))
                elif isinstance(edu, str) and edu.strip():
                    # Handle string education entries - skip empty ones
                    pass  # Drop empty strings
            normalized['education'] = new_edu
        
        # Ensure arrays are arrays
        for key in ['summary', 'experience', 'projects', 'education', 'certifications', 'awards']:
            if key in normalized and not isinstance(normalized[key], list):
                normalized[key] = []
        
        # Ensure contact is dict
        if 'contact' in normalized and not isinstance(normalized['contact'], dict):
            normalized['contact'] = {'email': '', 'phone': '', 'location': '', 'links': []}
        
        # Ensure skills is dict with groups
        if 'skills' in normalized and not isinstance(normalized['skills'], dict):
            normalized['skills'] = {'groups': []}
        
        return normalized

    def _extract_json(self, text: str) -> dict[str, Any]:
        """Extract JSON from AI response."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                raise ValueError("No JSON object found in model response.")
            return json.loads(match.group(0))

    def _compare_and_report(
        self,
        original: dict,
        modified: dict,
        change_type: str,
    ) -> ChangeReport:
        """Create a change report comparing two CV versions."""
        report = ChangeReport()
        
        # Track changes between original and modified
        for section in ["summary", "experience", "projects"]:
            orig_items = original.get(section, [])
            mod_items = modified.get(section, [])
            
            # If content was rewritten, track it as a change
            if str(orig_items) != str(mod_items):
                change = Change(
                    change_type=ChangeType.MODIFIED,
                    section=section,
                    item_key=f"{section}_0",
                    before_content=str(orig_items)[:100],
                    after_content=str(mod_items)[:100],
                    reason=f"{change_type}: Content enhanced for hiring-manager impact",
                    words_saved=0,
                    importance="HIGH"
                )
                report.add_change(change)
        
        return report

    def _interactive_review(
        self,
        optimized_cv: dict[str, Any],
        report: ChangeReport,
    ) -> dict[str, Any]:
        """Interactive review and approval of changes.
        
        Args:
            optimized_cv: Optimized CV
            report: Change report
            
        Returns:
            Final CV (optimized or reverted based on user choice)
        """
        while True:
            # Show summary
            self.review_system.display_changes_summary(report)

            # Get approval
            choice = self.review_system.prompt_for_approval()

            if choice == "approve":
                print("\n[OK] Changes approved!")
                return optimized_cv

            elif choice == "reject":
                print("\n[X] Changes rejected. Reverting to original CV.")
                return self.original_cv

            elif choice == "detail":
                self.review_system.display_detailed_changes(report)

            elif choice == "steer":
                steering = self.review_system.prompt_for_steering_instructions()
                if steering:
                    print(f"\n[->] Applying steering instructions...\n{steering}")
                    # Re-optimize with steering guidance
                    # This would be passed to the AI tailoring system
                    # For now, just continue with current optimized CV
                    return optimized_cv

    def save_optimization_report(self, report: ChangeReport) -> None:
        """Save optimization report to files.
        
        Args:
            report: ChangeReport to save
        """
        self.review_system.save_change_report(report)

    @staticmethod
    def _deep_copy(obj: Any) -> Any:
        """Create a deep copy."""
        import copy
        return copy.deepcopy(obj)


def build_with_config(
    cv_path: str | Path,
    config_path: str | Path,
    output_docx: str | Path,
    output_json: Optional[str | Path] = None,
    interactive: bool = False,
) -> None:
    """Build CV with intelligent optimization using config file.
    
    Args:
        cv_path: Path to input CV JSON
        config_path: Path to config file
        output_docx: Path for output DOCX
        output_json: Optional path for output JSON
        interactive: If True, show interactive review
    """
    # Load config
    print("Loading configuration...")
    config = load_config_from_file(config_path)
    print(f"[OK] Config loaded: {config.page_limit}-page CV")

    # Load CV
    print("Loading CV...")
    cv_json = load_json(cv_path)
    print(f"[OK] CV loaded: {cv_json.get('name', 'Unknown')}")

    # Create builder
    builder = IntelligentCVBuilder(cv_json, config)

    # Optimize
    print("Optimizing CV content...")
    optimized_cv, report = builder.optimize_for_page_limit(interactive=interactive)

    # Save report
    if report.changes:
        print("\nSaving optimization report...")
        builder.save_optimization_report(report)

    # Save optimized JSON if requested
    if output_json:
        save_json(optimized_cv, output_json)
        print(f"[OK] Saved optimized CV: {output_json}")

    # Build DOCX would happen here
    # build_docx(optimized_cv, output_docx)
    print(f"[OK] Ready to build DOCX: {output_docx}")

    return optimized_cv, report
