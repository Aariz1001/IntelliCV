# Quick Guide: Scraping Job Postings

## Automatic Scraping (works for most sites)

```bash
python -m src.main scrape-job "https://example.com/job/123" --output job.md
```

## For JavaScript-Heavy Sites (Ashby, Greenhouse, etc.)

If automatic scraping fails, use manual copy-paste:

### Method 1: Browser Copy
1. Open the job posting in your browser
2. Select all text (Ctrl+A)
3. Copy (Ctrl+C)  
4. Paste into a `.md` or `.txt` file

### Method 2: Browser "Reader Mode"
1. Open job posting
2. Press F9 or click Reader Mode icon
3. Copy the clean text
4. Save to file

### Method 3: Use the integrated workflow

```bash
# Step 1: Save job posting manually to a file (e.g., job.md)

# Step 2: Run CV Judge
python -m src.main judge --cv my_cv.txt --jd job.md

# Or combine with scraping if site works:
python -m src.main scrape-job "https://job-url" --output job.md
python -m src.main judge --cv my_cv.txt --jd job.md
```

## Full Workflow Example

```bash
# 1. Convert your DOCX CV to text
python scripts/docx_to_text.py "CV.docx" --output my_cv.txt

# 2. Try automatic scraping (or manually save job posting)
python -m src.main scrape-job "https://job-url" --output job.md

# 3. Run CV Judge analysis
python -m src.main judge --cv my_cv.txt --jd job.md --guidance "Focus on relevant skills"

# 4. Optional: Convert to structured JSON
python -m src.main cv-to-json --cv my_cv.txt --jd job.md --output analysis.json
```

## Supported Platforms

- ✅ Most standard job boards (works with Trafilatura)
- ✅ LinkedIn (copy-paste recommended)
- ✅ Indeed
- ⚠️ Ashby (manual copy-paste required)
- ⚠️ Greenhouse (manual copy-paste may be needed)
- ⚠️ Lever (manual copy-paste may be needed)
