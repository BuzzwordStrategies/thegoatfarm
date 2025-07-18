#!/bin/bash

echo "Starting The GOAT Farm Dashboard..."
echo "================================="

# Export environment variables
echo "Exporting environment variables..."
npm run export-env

# Check if export was successful
if [ $? -ne 0 ]; then
    echo "Failed to export environment variables. Please check your Python environment."
    exit 1
fi

# Start the dashboard server
echo ""
echo "Starting dashboard server..."
npm start 