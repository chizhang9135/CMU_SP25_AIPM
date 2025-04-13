#!/bin/bash

echo "🔐 Enter your OpenAI API key below."
echo "(Paste or type your key — input will be hidden for security):"
read -s OPENAI_KEY

# Safely write it to the .env file with single quotes
echo "OPENAI_API_KEY='$OPENAI_KEY'" > .env

echo "🚀 Starting the service..."
docker compose up --build
