#!/bin/bash

# Make sure pyenv is loaded
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# Set Python version
pyenv shell 3.13.6

# Start RSS parser
python /var/www/firefeed/data/integrations/telegram/rss_parser.py
