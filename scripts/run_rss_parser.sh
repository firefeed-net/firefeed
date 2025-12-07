#!/bin/bash

# Make sure pyenv is loaded
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
export PYTHONPATH="$HOME/firefeed/apps:$PYTHONPATH"
eval "$(pyenv init -)"

# Set Python version
pyenv shell 3.13.6

# Start RSS parser
python -m apps.rss_parser
