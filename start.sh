#!/bin/bash
if [ -f .env ]; then
  source .env
fi
# Values of environment variables can be overridden by assigning values to names below
export DISCORD_TOKEN
export DISCORD_PREFIX
export LANG
python3 bot.py
read -p "Press any key to continue . . . "
