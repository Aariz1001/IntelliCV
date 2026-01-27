# CV Builder CLI

> **AI-powered CV Builder with GitHub integration, chatbot interface, and hiring-manager focused optimization**

```
 ██████╗██╗   ██╗    ██████╗ ██╗   ██╗██╗██╗     ██████╗ ███████╗██████╗
██╔════╝██║   ██║    ██╔══██╗██║   ██║██║██║     ██╔══██╗██╔════╝██╔══██╗
██║     ██║   ██║    ██████╔╝██║   ██║██║██║     ██║  ██║█████╗  ██████╔╝
██║     ╚██╗ ██╔╝    ██╔══██╗██║   ██║██║██║     ██║  ██║██╔══╝  ██╔══██╗
╚██████╗ ╚████╔╝     ██████╔╝╚██████╔╝██║███████╗██████╔╝███████╗██║  ██║
 ╚═════╝  ╚═══╝      ╚═════╝  ╚═════╝ ╚═╝╚══════╝╚═════╝ ╚══════╝╚═╝  ╚═╝
```

## Installation

```bash
# Global install (recommended)
npm install -g cv-builder-ai

# Or install locally
cd cli
npm install
npm link
```

After installation, you can run from anywhere:
```bash
cv-builder        # Launch interactive menu
cv-builder chat   # Start AI chatbot
cvb               # Shorthand alias
```

## Features

- **Interactive Menu** - Arrow-key navigation with visual feedback
- **AI Chatbot** - Natural language interface with function calling
- **Slash Commands** - Quick access to all features via /commands
- **GitHub Integration** - Pull README files as proof of work
- **One-Click Enhancement** - Optimize + AI tailor in a single step
- **Professional DOCX** - Generate ATS-friendly Word documents

## Quick Start

### Interactive Menu
```bash
cv-builder
```

### AI Chatbot
```bash
cv-builder chat
```

In the chatbot, you can:
- Type naturally: "enhance my CV for a software engineer role"
- Use slash commands: `/help`, `/enhance`, `/status`
- Load files: `/load my_cv.json`
- View files: `/files`

### Direct Commands
```bash
cv-builder convert "My CV.docx" -o my_cv.json
cv-builder fetch
cv-builder enhance my_cv.json -o enhanced.json
cv-builder build enhanced.json -o final.docx
cv-builder status
```

## Slash Commands (Chat Mode)

| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/status` | Check workflow status |
| `/convert` | Convert DOCX to JSON |
| `/fetch` | Download GitHub READMEs |
| `/optimize` | Fit CV to page limit |
| `/enhance` | Full CV enhancement |
| `/build` | Generate Word document |
| `/quick` | One-click workflow |
| `/config` | View configuration |
| `/files` | List CV and README files |
| `/load <n>` | Load a CV into context |
| `/clear` | Clear chat history |
| `/exit` | Exit chatbot |

## Menu Options

| Key | Option | Description |
|-----|--------|-------------|
| Q | Quick Enhance | One-click full pipeline |
| C | Convert DOCX | Extract CV structure to JSON |
| F | Fetch GitHub | Download README files |
| O | Optimize | Fit to page limit |
| T | AI Tailor | Enhance with AI + GitHub |
| E | Full Enhance | Optimize + AI combined |
| B | Build DOCX | Generate Word document |
| A | AI Chat | Interactive chatbot |
| S | Settings | View configuration |
| ? | Status | Check workflow progress |
| X | Exit | Quit application |

## Requirements

- Node.js 18+
- Python 3.10+ (for backend)
- `.env` file with:
  - `OPENROUTER_API_KEY` - For AI features
  - `GITHUB_TOKEN` - For fetching READMEs

## Architecture

```
+----------------------------------+
|     Node.js CLI (Frontend)       |
|  - Interactive menus             |
|  - AI Chatbot with /commands     |
|  - Function calling              |
+----------------+-----------------+
                 |
                 v
+----------------------------------+
|     Python Backend               |
|  - DOCX parsing                  |
|  - AI optimization               |
|  - GitHub integration            |
+----------------------------------+
```

## License

MIT
