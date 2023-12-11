#!/bin/bash

# Stop the FastAPI service
sudo systemctl stop wealth-sync.service

# Fetch new code from your repository (replace with the appropriate git command)
git fetch origin
git reset --hard origin/master


source myenv/bin/activate
pip install -r requirements.txt

chmod +x main.sh
chmod +x restart.sh
chmod +x livefeed.sh

# Restart the FastAPI service
sudo systemctl start wealth-sync.service