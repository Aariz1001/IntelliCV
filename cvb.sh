#!/bin/bash
cd "$(dirname "$0")/cli"
node src/index.js "$@"
