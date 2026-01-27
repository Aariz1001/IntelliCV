# CV Judge - Ensemble AI CV Analyzer

## Overview

CV Judge is an advanced AI-powered CV screening tool that uses an **ensemble of three different AI models** to provide unbiased, comprehensive candidate evaluations. By leveraging multiple AI perspectives (Claude 3.5 Sonnet, GPT-4o Mini, and Gemini 1.5 Flash), it eliminates single-model bias and provides triangulated, evidence-based assessments.

## Features

✨ **Multi-Model Ensemble**
- Claude 3.5 Sonnet (Reasoning Lead - 40% weight)
- GPT-4o Mini (Efficiency - 30% weight)  
- Gemini 1.5 Flash (Validation - 30% weight)

🎯 **Evidence-Based Analysis**
- Chain-of-Thought prompting for transparent reasoning
- Verbatim evidence extraction from source documents
- No hallucinated qualifications

⚡ **High Performance**
- Async/parallel API calls for minimal latency
- Typical analysis completes in 5-10 seconds
- Automatic retry with exponential backoff

🎨 **Rich Terminal Output**
- Color-coded consensus scores
- Detailed breakdown tables
- Consensus highlights and discordance warnings
- Individual judge rationales

🔒 **Privacy-First**
- All processing via OpenRouter API
- No data storage on servers
- Local-first execution

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set your OpenRouter API key
export OPENROUTER_API_KEY="your-api-key-here"

# Or add to .env file
echo "OPENROUTER_API_KEY=your-api-key-here" >> .env
```

## Usage

### Basic Usage

```bash
python -m src.main judge --cv path/to/cv.md --jd path/to/job_description.md
```

### With Custom Guidance

```bash
python -m src.main judge \
  --cv sample_cv.md \
  --jd sample_jd.md \
  --guidance "Focus heavily on ML/AI experience and cloud architecture skills"
```

### Using URLs

```bash
python -m src.main judge \
  --cv https://example.com/my-cv \
  --jd https://careers.company.com/job/12345
```

## How It Works

### 1. Content Ingestion
The system accepts CVs and job descriptions in multiple formats:
- Local files (`.txt`, `.md`)
- URLs (automatically extracts clean text using Trafilatura)

### 2. Parallel Evaluation
Three AI models evaluate the CV simultaneously:
- **Claude 3.5 Sonnet**: Provides deep reasoning and nuanced analysis
- **GPT-4o Mini**: Efficient extraction and pattern matching
- **Gemini 1.5 Flash**: Independent validation from Google's perspective

Each judge receives a Chain-of-Thought prompt that asks them to:
1. Extract 3-5 key requirements from the JD
2. Find verbatim evidence in the CV
3. Identify matching skills and gaps
4. Note red flags and strengths
5. Provide a 0-100 score with rationale

### 3. Consensus Aggregation
The system:
- Calculates a **weighted average score** (based on model strengths)
- Identifies **consensus points** where all models agree
- Flags **discordance** if scores vary by >25 points
- Generates a final hiring recommendation

### 4. Rich Report Generation
Outputs include:
- Consensus score with color coding (red/yellow/green)
- Recommendation (Strong Recommend / Recommend / Consider / Not Recommended)
- Consensus highlights
- Points of disagreement
- Detailed table of each judge's evaluation
- Full rationales from each model

## Example Output

```
╭─────────────────── CV Judge Ensemble Report ───────────────────╮
│            Consensus Score: 87.3/100                           │
╰────────────────────────────────────────────────────────────────╯

## ✅ Strong Recommend - Excellent match with consensus score of 87.3.
Candidate demonstrates strong alignment with job requirements.

✨ Consensus Highlights:
  • Universally recognized skills: Python, Kubernetes, AWS, ML/AI
  • All models strongly recommend this candidate

Individual Judge Evaluations:
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Judge              ┃ Score  ┃ Key Insights                  ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Claude 3.5 Sonnet  │   88   │ ✓ Skills: Python, AWS, K8s   │
│                    │        │ ✗ Missing: Go experience      │
│ GPT-4o Mini        │   85   │ ✓ Skills: ML pipelines, CI/CD│
│                    │        │ ✓ Strong cloud background     │
│ Gemini 1.5 Flash   │   89   │ ✓ Skills: Microservices, DB  │
│                    │        │ ✓ Excellent problem solving   │
└────────────────────┴────────┴──────────────────────────────┘
```

## Configuration

### Model Weights
Default weights are set in `src/judge_orchestrator.py`:
```python
MODELS = {
    "claude": {"weight": 0.4},   # Reasoning lead
    "gpt": {"weight": 0.3},      # Efficiency
    "gemini": {"weight": 0.3}    # Validation
}
```

### Discordance Threshold
Set in `src/consensus_aggregator.py`:
```python
DISCORDANCE_THRESHOLD = 25  # Score variance to flag disagreement
```

## Architecture

```
┌─────────────────┐
│   CLI Input     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Content Ingestor │ (URLs → Clean Text)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Judge Orchestrator│ ────┬──► Claude 3.5 Sonnet
│  (Async/Await)  │      ├──► GPT-4o Mini
└────────┬────────┘      └──► Gemini 1.5 Flash
         │
         ▼
┌─────────────────┐
│Data Aggregator  │ (Weighted Average + Validation)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Rich Formatter  │ (Terminal Tables + Colors)
└─────────────────┘
```

## API Costs

Using OpenRouter with typical CV/JD pair (~5K tokens):
- Claude 3.5 Sonnet: ~$0.015
- GPT-4o Mini: ~$0.002
- Gemini 1.5 Flash: ~$0.001

**Total per evaluation: ~$0.02**

Batch processing 100 CVs: ~$2.00

## Error Handling

- **Rate Limiting**: Automatic exponential backoff (3 retries)
- **Malformed JSON**: Attempts repair, excludes failed judge from consensus
- **Network Errors**: Graceful degradation with partial results
- **Model Failures**: Continues with remaining judges if 1 fails

## Troubleshooting

### "OpenRouter API key required"
Set the environment variable:
```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
```

### "trafilatura not installed"
Install web scraping dependencies:
```bash
pip install trafilatura
```

### Models returning low-quality responses
Try adjusting the temperature in `judge_orchestrator.py`:
```python
"temperature": 0.1  # Lower = more focused
```

## Roadmap

- [ ] PDF CV support
- [ ] Batch mode (analyze 100+ CVs against one JD)
- [ ] JSON export of reports
- [ ] Custom model selection
- [ ] Local LLM support (Ollama)
- [ ] Web UI interface

## Credits

Built following the architectural principles from the [plan](plan/) directory.

## License

See main project LICENSE file.
