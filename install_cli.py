#!/usr/bin/env python
"""Update requirements.txt with Typer dependencies."""

import subprocess
import sys

packages = [
    "typer[all]",
    "rich",
]

for package in packages:
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

print("✓ Dependencies installed")
