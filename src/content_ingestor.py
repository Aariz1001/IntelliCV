"""Content ingestion module for extracting text from various sources."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Tuple

try:
    import trafilatura
    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class ContentIngestor:
    """Handles extraction of text from files and URLs."""
    
    @staticmethod
    def is_url(text: str) -> bool:
        """Check if a string is a URL."""
        return text.startswith(("http://", "https://"))
    
    @staticmethod
    def extract_from_file(file_path: str | Path) -> str:
        """Extract text content from a local file.
        
        Args:
            file_path: Path to the file (.txt, .md, or similar text file)
            
        Returns:
            The text content of the file
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file type is not supported
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Support text and markdown files
        supported_extensions = {".txt", ".md", ".markdown"}
        if path.suffix.lower() not in supported_extensions:
            raise ValueError(
                f"Unsupported file type: {path.suffix}. "
                f"Supported types: {', '.join(supported_extensions)}"
            )
        
        return path.read_text(encoding="utf-8")
    
    @staticmethod
    def extract_from_url(url: str) -> str:
        """Extract clean text content from a URL.
        
        Args:
            url: The URL to fetch and extract content from
            
        Returns:
            Clean text extracted from the webpage
            
        Raises:
            ValueError: If required dependencies are not installed
            RuntimeError: If the URL cannot be fetched or parsed
        """
        if not REQUESTS_AVAILABLE:
            raise ValueError(
                "The 'requests' library is required for URL fetching. "
                "Install it with: pip install requests"
            )
        
        if not TRAFILATURA_AVAILABLE:
            raise ValueError(
                "The 'trafilatura' library is required for web content extraction. "
                "Install it with: pip install trafilatura"
            )
        
        try:
            # Fetch the URL with a user agent
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Extract clean text using trafilatura
            extracted = trafilatura.extract(
                response.content,
                include_comments=False,
                include_tables=True,
                no_fallback=False
            )
            
            if not extracted:
                raise RuntimeError(f"Could not extract text from URL: {url}")
            
            return extracted
            
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch URL {url}: {str(e)}")
    
    @staticmethod
    def load_content(source: str | Path) -> Tuple[str, str]:
        """Load content from either a file or URL.
        
        Args:
            source: Either a file path or URL
            
        Returns:
            Tuple of (content, source_type) where source_type is "file" or "url"
            
        Raises:
            ValueError: If the source is invalid or cannot be processed
        """
        source_str = str(source)
        
        if ContentIngestor.is_url(source_str):
            return ContentIngestor.extract_from_url(source_str), "url"
        else:
            return ContentIngestor.extract_from_file(source), "file"
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text content.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text with normalized whitespace
        """
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Remove common artifacts
        text = text.strip()
        
        return text
