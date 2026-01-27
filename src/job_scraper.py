"""
Advanced job posting scraper with BeautifulSoup4 and fallback strategies.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import requests

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    import trafilatura
    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False


class JobScraper:
    """Advanced job posting scraper with multiple fallback strategies."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize scraped text."""
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        text = text.strip()
        
        # Remove navigation/footer noise
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if len(line) < 3:
                continue
            if line.lower() in ['home', 'about', 'careers', 'apply', 'share', 'save']:
                continue
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _scrape_with_bs4(self, url: str) -> Optional[str]:
        """Scrape with BeautifulSoup4 for better HTML parsing."""
        if not BS4_AVAILABLE:
            return None
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(['script', 'style', 'nav', 'header', 'footer']):
                script.decompose()
            
            # Try to find main content area
            main_content = None
            
            # Common job posting containers
            selectors = [
                ('div', {'class': lambda x: x and ('job' in str(x).lower() or 'description' in str(x).lower())}),
                ('div', {'id': lambda x: x and ('job' in str(x).lower() or 'description' in str(x).lower())}),
                ('article', {}),
                ('main', {}),
                ('div', {'role': 'main'}),
            ]
            
            for tag, attrs in selectors:
                main_content = soup.find(tag, attrs)
                if main_content:
                    break
            
            if not main_content:
                main_content = soup.body if soup.body else soup
            
            # Convert to markdown-like text
            md_text = self._html_to_markdown(main_content)
            
            if md_text and len(md_text) > 100:
                return self._clean_text(md_text)
                
        except Exception as e:
            print(f"BeautifulSoup4 failed: {e}")
        
        return None
    
    def _html_to_markdown(self, element) -> str:
        """Convert HTML element to markdown-like text."""
        if not BS4_AVAILABLE:
            return ""
        
        text_parts = []
        
        for child in element.descendants:
            if child.name is None:
                # Text node
                text = str(child).strip()
                if text:
                    text_parts.append(text)
            elif child.name == 'h1':
                text_parts.append(f"\n# {child.get_text().strip()}\n")
            elif child.name == 'h2':
                text_parts.append(f"\n## {child.get_text().strip()}\n")
            elif child.name == 'h3':
                text_parts.append(f"\n### {child.get_text().strip()}\n")
            elif child.name == 'h4':
                text_parts.append(f"\n#### {child.get_text().strip()}\n")
            elif child.name == 'li':
                text_parts.append(f"- {child.get_text().strip()}\n")
            elif child.name == 'p':
                text_parts.append(f"\n{child.get_text().strip()}\n")
            elif child.name == 'br':
                text_parts.append("\n")
        
        # Fallback: just get all text
        if not text_parts:
            return element.get_text(separator='\n', strip=True)
        
        result = ''.join(text_parts)
        # Clean up excessive newlines
        result = re.sub(r'\n\s*\n\s*\n+', '\n\n', result)
        return result
    
    def _scrape_with_trafilatura(self, url: str) -> Optional[str]:
        """Try scraping with trafilatura."""
        if not TRAFILATURA_AVAILABLE:
            return None
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            extracted = trafilatura.extract(
                response.content,
                include_comments=False,
                include_tables=True,
                no_fallback=False,
                favor_precision=False,
                favor_recall=True
            )
            
            if extracted and len(extracted) > 100:
                return self._clean_text(extracted)
        except Exception as e:
            print(f"Trafilatura failed: {e}")
        
        return None
    
    def scrape(self, url: str) -> str:
        """Scrape job posting with multiple fallback strategies.
        
        Args:
            url: URL of the job posting
            
        Returns:
            Cleaned text content
            
        Raises:
            RuntimeError: If all scraping methods fail
        """
        print(f"Scraping: {url}")
        
        # Strategy 1: BeautifulSoup4 (best for HTML parsing)
        print("  → Trying BeautifulSoup4...")
        content = self._scrape_with_bs4(url)
        if content:
            print("  [OK] Success with BeautifulSoup4")
            return content
        
        # Strategy 2: Trafilatura (fallback)
        print("  → Trying Trafilatura...")
        content = self._scrape_with_trafilatura(url)
        if content:
            print("  [OK] Success with Trafilatura")
            return content
        
        raise RuntimeError(
            f"Failed to scrape {url}. The site may require manual copy-paste.\n"
            f"Make sure you have beautifulsoup4 installed: pip install beautifulsoup4"
        )
    
    def scrape_and_save(self, url: str, output_path: str | Path) -> str:
        """Scrape job posting and save to markdown file.
        
        Args:
            url: URL of the job posting
            output_path: Path to save the markdown file
            
        Returns:
            The scraped content
        """
        content = self.scrape(url)
        
        output_file = Path(output_path)
        output_file.write_text(content, encoding='utf-8')
        
        print(f"\n[OK] Saved to: {output_path}")
        print(f"  Characters: {len(content)}")
        
        return content


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Scrape job postings from various platforms"
    )
    parser.add_argument("url", help="URL of the job posting")
    parser.add_argument(
        "--output", "-o",
        help="Output markdown file path (default: job_posting.md)",
        default="job_posting.md"
    )
    
    args = parser.parse_args()
    
    scraper = JobScraper()
    
    try:
        scraper.scrape_and_save(args.url, args.output)
    except Exception as e:
        print(f"\n[X] Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
