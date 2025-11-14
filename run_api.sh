#!/bin/bash

# Make sure pyenv is loaded
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# Set Python version
pyenv shell 3.13.6

# Start FastAPI via uvicorn
uvicorn api.main:app --host 127.0.0.1 --port 8000
