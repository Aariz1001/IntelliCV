#!/bin/bash
# CV Builder launcher for macOS/Linux

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install/update dependencies
echo "Ensuring dependencies are installed..."
pip install -q -r requirements.txt

# Run the CLI
python -m src.main "$@"
