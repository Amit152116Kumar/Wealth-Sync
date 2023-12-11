#!/bin/bash

# Get the current time in 24-hour format (HHMM)
current_time=$(date +%H%M)

# Define the target times in HHMM format
first_cmd_time="0900"   # 9:00 AM
second_cmd_time="1530"  # 3:30 PM

# Compare the current time with target times
if [ "$current_time" -lt "$first_cmd_time" ]; then
    curl -X GET http://localhost:8080/fetchTokens
fi

if [ "$current_time" -ge "$first_cmd_time" ] && [ "$current_time" -lt "$second_cmd_time" ]; then
    # Run the first command
    curl -X GET http://localhost:8080/subscribe
    # Add your first command here
fi

if [ "$current_time" -ge "$second_cmd_time" ]; then
    # Run the second command
    curl -X GET http://localhost:8080/unsubscribe
    # Add your second command here
fi

# If you want to add an "else" block for actions before the specified times, you can do so here.
