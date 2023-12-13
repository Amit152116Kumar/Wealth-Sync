#!/bin/bash

# Fetch changes from the remote repository
git fetch origin

# Check if there are new commits in the remote repository
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u})
BASE=$(git merge-base @ @{u})

if [ $LOCAL = $REMOTE ]; then
    echo "Up-to-date"
elif [ $LOCAL = $BASE ]; then
    echo "Need to pull"

    # Stop the FastAPI service
    sudo systemctl stop wealth-sync.service

    # Reset local code to match remote repository
    git reset --hard origin/master

    # Activate virtual environment and install requirements
    source myenv/bin/activate
    pip install -r requirements.txt

    # Set execute permissions on scripts
    chmod +x main.sh
    chmod +x restart.sh
    chmod +x livefeed.sh

    # Restart the FastAPI service
    sudo systemctl start wealth-sync.service
else
    echo "Diverged"
fi