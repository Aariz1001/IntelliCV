"""
Convert DOCX CV to plain text for CV Judge analysis.

Usage:
    python scripts/docx_to_text.py "CV of Aariz Waqas (1).docx" --output my_cv.txt
"""

from __future__ import annotations

import argparse
from pathlib import Path

from docx import Document


def extract_text_from_docx(docx_path: str | Path) -> str:
    """Extract all text from a DOCX file.
    
    Args:
        docx_path: Path to the DOCX file
        
    Returns:
        Extracted text with paragraph breaks preserved
    """
    doc = Document(docx_path)
    
    paragraphs = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            paragraphs.append(text)
    
    return "\n\n".join(paragraphs)


def main():
    parser = argparse.ArgumentParser(description="Convert DOCX CV to plain text")
    parser.add_argument("docx", help="Path to DOCX file")
    parser.add_argument("--output", "-o", help="Output text file path")
    
    args = parser.parse_args()
    
    # Extract text
    text = extract_text_from_docx(args.docx)
    
    # Save or print
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(text, encoding="utf-8")
        print(f"✓ Text extracted to: {args.output}")
        print(f"  Total characters: {len(text)}")
    else:
        print(text)


if __name__ == "__main__":
    main()
