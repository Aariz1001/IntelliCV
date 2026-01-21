# IntelliCV

An intelligent CV builder that transforms your career data into a professionally-tailored, ATS-optimized Word document using AI. Upload your CV, select GitHub repos, and get a one-page resume optimized for both applicant tracking systems and hiring managers.

## 🚀 Features

- **JSON-based CV input** - Structured, version-controllable CV format
- **GitHub integration** - Download READMEs from public & private repos (with GitHub token)
- **AI-powered tailoring** - Uses OpenRouter's `google/gemini-3-flash-preview` with high reasoning effort
- **ATS optimization** - Keyword injection, metric-driven bullets, impact-focused writing
- **Professional formatting** - One-page layout with 0.25" margins, compact spacing, styled sections
- **DOCX conversion** - Convert your existing DOCX CV to JSON format for easy editing
- **Interactive CLI** - Choose repos on the fly, download READMEs, and generate tailored CVs in seconds

## 📋 Table of Contents

- [Installation](#installation)
- [Setup](#setup)
- [Usage](#usage)
  - [Convert DOCX to JSON](#convert-docx-to-json)
  - [Interactive Mode (Recommended)](#interactive-mode-recommended)
  - [Fetch READMEs](#fetch-readmes)
  - [Build from Existing Files](#build-from-existing-files)
- [File Formats](#file-formats)
- [Configuration](#configuration)
- [Examples](#examples)
- [Tips & Best Practices](#tips--best-practices)

## 🛠️ Installation

### Prerequisites
- Python 3.10+
- Git

### Clone & Setup

```bash
git clone <repo-url>
cd CV_Builder
python -m venv venv
.\venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
```

## ⚙️ Setup

### 1. Environment Variables

Copy the example file and fill in your API keys:

```bash
copy .env.example .env
```

Edit `.env`:

```env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxx
OPENROUTER_MODEL=google/gemini-3-flash-preview
OPENROUTER_REASONING_EFFORT=high
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxx
OPENROUTER_HTTP_REFERER=
OPENROUTER_X_TITLE=
```

### 2. Get Your API Keys

**OpenRouter API Key:**
- Visit [openrouter.ai/keys](https://openrouter.ai/keys)
- Sign in or create an account
- Generate a new API key
- Copy it to `OPENROUTER_API_KEY` in `.env`

**GitHub Token (optional, required for private repos):**
- Go to [github.com/settings/tokens](https://github.com/settings/tokens)
- Click "Generate new token (classic)"
- Select `repo` scope
- Copy it to `GITHUB_TOKEN` in `.env`

## 📖 Usage

### Convert DOCX to JSON

If you already have a DOCX CV, convert it to JSON for editing:

```bash
.\venv\Scripts\python scripts\docx_to_json.py "Your CV.docx" --output my_cv.json
```

### Interactive Mode (Recommended)

The fastest way to build a tailored CV:

```bash
.\venv\Scripts\python -m src.main interactive --cv my_cv.json --repos repos.txt --output-docx tailored_cv.docx
```

**What happens:**
1. Lists all repos from `repos.txt`
2. You select which ones to use: `1,3,5` or `1-3` or `all` or `none`
3. Downloads & caches selected READMEs
4. Tailors your CV using AI (high reasoning effort)
5. Generates a professional one-page DOCX

### Fetch READMEs (Separate Step)

Download READMEs upfront for a specific set of repos:

```bash
.\venv\Scripts\python -m src.main fetch-readmes --repos repos.txt --out .readme_cache
```

Repos file format (`repos.txt`):
```
microsoft/vscode
facebook/react
# Comments are ignored
google/go
```

### Build from Existing Files

If you already have READMEs locally:

```bash
.\venv\Scripts\python -m src.main build \
  --cv my_cv.json \
  --readme-dir ./readmes \
  --output-docx output.docx
```

Or use individual README files:

```bash
.\venv\Scripts\python -m src.main build \
  --cv my_cv.json \
  --readme ./project1/README.md \
  --readme ./project2/README.md \
  --output-docx output.docx
```

## 📄 File Formats

### Input CV JSON (`my_cv.json`)

```json
{
  "name": "Jane Doe",
  "title": "Senior Software Engineer",
  "contact": {
    "email": "jane@example.com",
    "phone": "+1 555 555 5555",
    "location": "Remote",
    "links": [
      {"label": "GitHub", "url": "https://github.com/jane"},
      {"label": "LinkedIn", "url": "https://linkedin.com/in/jane"}
    ]
  },
  "summary": [
    "5+ years building scalable web platforms",
    "Experienced in Python and cloud architecture"
  ],
  "experience": [
    {
      "company": "Acme Inc.",
      "role": "Senior Engineer",
      "location": "Remote",
      "dates": "2021 - Present",
      "bullets": [
        "Built and deployed microservices handling 100K+ requests/sec",
        "Reduced API latency by 40% through caching and optimization"
      ]
    }
  ],
  "projects": [
    {
      "name": "Analytics Dashboard",
      "link": "https://github.com/jane/analytics",
      "dates": "2020",
      "bullets": [
        "Real-time data visualization for internal teams"
      ]
    }
  ],
  "education": [
    {
      "school": "State University",
      "degree": "B.S. Computer Science",
      "location": "City, ST",
      "dates": "2016 - 2020",
      "details": ["Graduated with honors"]
    }
  ],
  "skills": {
    "groups": [
      {"name": "Languages", "items": ["Python", "TypeScript", "SQL"]},
      {"name": "Frameworks", "items": ["FastAPI", "React"]}
    ]
  },
  "certifications": ["AWS Certified Developer"],
  "awards": []
}
```

**Required fields:**
- `name`, `title`
- `contact.email`
- `summary` (array)
- `experience` (array)
- `skills.groups` (array)

### Repos File (`repos.txt`)

```
# List repos to download READMEs from
owner/repo-name
microsoft/vscode
facebook/react
# Private repos work if GITHUB_TOKEN is set
your-org/private-repo
```

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | ✅ Yes | - | Your OpenRouter API key |
| `OPENROUTER_MODEL` | No | `google/gemini-3-flash-preview` | AI model to use |
| `OPENROUTER_REASONING_EFFORT` | No | `high` | Reasoning effort: `low`, `medium`, `high` |
| `GITHUB_TOKEN` | No | - | GitHub PAT for private repo access |
| `OPENROUTER_HTTP_REFERER` | No | - | Optional referer header |
| `OPENROUTER_X_TITLE` | No | - | Optional title header |

## 📚 Examples

### Example 1: Convert & Tailor Existing CV

```bash
# Step 1: Convert your DOCX CV to JSON
.\venv\Scripts\python scripts\docx_to_json.py "My Resume.docx" --output my_cv.json

# Step 2: Create repos.txt with your projects
echo microsoft/vscode > repos.txt
echo facebook/react >> repos.txt

# Step 3: Run interactive mode
.\venv\Scripts\python -m src.main interactive --cv my_cv.json --repos repos.txt --output-docx tailored.docx
```

### Example 2: Use Pre-downloaded READMEs

```bash
# Pre-download and cache READMEs
.\venv\Scripts\python -m src.main fetch-readmes --repos repos.txt --out ./readmes

# Then build multiple times without re-downloading
.\venv\Scripts\python -m src.main build --cv my_cv.json --readme-dir ./readmes --output-docx output.docx
```

### Example 3: No READMEs (just optimize existing CV)

```bash
# If you don't have repos, it still works - just optimizes what you have
.\venv\Scripts\python -m src.main build --cv my_cv.json --output-docx optimized.docx
```

## 💡 Tips & Best Practices

### ATS Optimization

The AI automatically:
- **Adds metrics** to every bullet (percentages, time saved, users impacted)
- **Injects keywords** like Python, AI, LLM, RAG, Cloud, GCP, AWS
- **Uses power verbs** like Architected, Engineered, Optimized, Deployed
- **Keeps one-page layout** with tight spacing (0.25" margins)

### For Best Results

1. **Be specific in your CV JSON** - More details = better tailoring
2. **Include all projects** - Even non-GitHub projects (they'll be preserved)
3. **Add metrics** - "Reduced latency by 40%" beats "Improved performance"
4. **Select relevant repos** - Choose 2-5 repos that align with your strengths
5. **Review the output** - Edit `my_cv.json` to fix anything before regenerating

### Customization

- **Edit `.env`** to change the AI model, reasoning effort, or OpenRouter settings
- **Edit `my_cv.json`** directly to add/remove details before tailoring
- **Edit `repos.txt`** to point to different GitHub repositories

## 🔒 Security

- API keys are stored in `.env` (excluded via `.gitignore`)
- GitHub token is only used to download public/private READMEs
- No data is stored beyond local cache directory
- `.readme_cache/` is excluded from git

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'src'"
Run from the project root, not from inside `src/`:
```bash
cd CV_Builder
.\venv\Scripts\python -m src.main --help
```

### "ImportError: attempted relative import"
Same issue - run from project root with `-m src.main`.

### "Missing OPENROUTER_API_KEY"
Check that `.env` exists and has a valid key:
```bash
cat .env | grep OPENROUTER_API_KEY
```

### "README not found for owner/repo"
- Check the repo name is correct
- For private repos, ensure `GITHUB_TOKEN` is set and has repo scope

## 📦 Requirements

See [requirements.txt](requirements.txt) for dependencies:
- `requests` - GitHub API calls
- `python-docx` - DOCX generation
- `jsonschema` - CV schema validation
- `python-dotenv` - Environment variables

## 📝 License

MIT License - feel free to use and modify.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Support

For issues, questions, or suggestions, open a GitHub issue.

