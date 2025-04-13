#!/bin/bash

echo "Welcome to the PDF-to-YAML Schema Converter."
read -p "Please paste your OpenAI API key: " USER_KEY

# Create .env dynamically
echo "OPENAI_API_KEY=$USER_KEY" > .env

echo "Starting the service..."
docker-compose up --build
