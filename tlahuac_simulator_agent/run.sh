#!/bin/bash
# Helper script to run Python scripts with virtual environment activated

# Activate virtual environment
source venv/bin/activate

# Run the provided command
exec "$@"
