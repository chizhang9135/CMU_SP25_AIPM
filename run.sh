#!/bin/bash

echo "🔐 Enter your OpenAI API key:"
read -s OPENAI_KEY

# Safely write it to the .env file with single quotes
echo "OPENAI_API_KEY='$OPENAI_KEY'" > .env

echo "🚀 Starting the service..."
docker compose up --build
