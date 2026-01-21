# GitHub Deployment Checklist

Your CV Builder project is ready for GitHub! Follow these steps to push it to a GitHub repository.

## Pre-Deployment

- [x] `.gitignore` configured (Python, venv, .env, generated files)
- [x] `.env.example` provided with placeholder values
- [x] `requirements.txt` includes all dependencies
- [x] `pyproject.toml` configured for packaging
- [x] `README.md` with comprehensive documentation
- [x] `CHANGELOG.md` tracking releases
- [x] `CONTRIBUTING.md` for contributors
- [x] Initial git commit created

## Steps to Deploy

### 1. Create Repository on GitHub

1. Go to [github.com/new](https://github.com/new)
2. Enter repository name: `cv-builder`
3. Add description: "AI-powered CV builder using OpenRouter and GitHub READMEs"
4. Choose visibility: **Public** or **Private**
5. Do NOT initialize with README/gitignore (we have them)
6. Click "Create repository"

### 2. Push to GitHub

```bash
cd "c:\Users\maari\Desktop\CV_Builder"

# Add remote origin (replace username/repo)
git remote add origin https://github.com/yourusername/cv-builder.git

# Rename branch to main if needed
git branch -M main

# Push to GitHub
git push -u origin main
```

### 3. Verify on GitHub

- [ ] All files appear in the repository
- [ ] README.md displays correctly
- [ ] `.gitignore` is present
- [ ] No `.env` file (should be in .gitignore)
- [ ] No `__pycache__` or `.venv` folders

## Optional: Additional Setup

### Add GitHub Topics
On your repository page → Settings → Topics, add:
- `cv`
- `resume`
- `ai`
- `openrouter`
- `gemini`

### Add LICENSE File
Create `LICENSE` file with MIT license text. GitHub can auto-generate this.

### Enable Issues & Discussions
Settings → Features → Enable Issues and Discussions

### Add Repository Description
Go to repository settings and add:
- Description
- Website (if applicable)
- Topics

### Configure Branch Protection (Optional)
For professional repos:
1. Settings → Branches
2. Add rule for `main` branch
3. Require pull request reviews
4. Require status checks

## Using pip to Install

Once published, users can install with:

```bash
# From git
pip install git+https://github.com/yourusername/cv-builder.git

# From PyPI (after publishing)
pip install cv-builder
```

## Publishing to PyPI (Optional)

To make it installable via `pip install cv-builder`:

```bash
# Install build tools
pip install build twine

# Build distribution
python -m build

# Upload to PyPI
twine upload dist/*
```

You'll need a PyPI account at [pypi.org](https://pypi.org)

## Troubleshooting

### "fatal: remote origin already exists"
```bash
git remote remove origin
git remote add origin https://github.com/yourusername/cv-builder.git
```

### "Permission denied (publickey)"
Set up SSH keys: [GitHub SSH Setup](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)

Or use HTTPS with GitHub token instead:
```bash
git remote set-url origin https://yourusername:ghp_token@github.com/yourusername/cv-builder.git
```

### Changes not pushed?
```bash
git status  # Check what's not committed
git add .   # Stage changes
git commit -m "Your message"
git push
```

## Next Steps

1. Create GitHub Actions for CI/CD (optional)
2. Add badges to README (build status, license, etc.)
3. Create releases and tags
4. Publish documentation (GitHub Pages)
5. Announce on Twitter, Reddit, HN

## Maintenance

- Keep dependencies updated: `pip list --outdated`
- Monitor for security issues in dependencies
- Review and merge PRs promptly
- Release updates regularly
- Update CHANGELOG.md with each release
