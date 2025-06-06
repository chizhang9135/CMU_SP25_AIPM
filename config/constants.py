"""
Constants used throughout the application.
"""
import os
from dotenv import load_dotenv
load_dotenv()

# OpenAI API configuration
OPENAI_API_KEY_ENV_NAME = "OPENAI_API_KEY"
OPENAI_API_KEY = os.getenv(OPENAI_API_KEY_ENV_NAME)
if not OPENAI_API_KEY:
    raise ValueError(f"Environment variable {OPENAI_API_KEY_ENV_NAME} is not set. Please set it in your .env file.")
OPENAI_MODEL = "gpt-4o-mini"

# Temperature controls randomness in the model's responses:
# - 0.0: Focused, deterministic responses (good for structured data)
# - 0.5: Balanced creativity and consistency
# - 1.0: Maximum creativity and randomness
# For our schema parsing, we want consistent, structured output,
# so we use a low temperature value
OPENAI_TEMPERATURE = 0.2

# File Paths
DEFAULT_PROMPT_TEMPLATE = "config/prompts/schema_to_dataset.txt"
DEFAULT_SCHEMA_VALIDATOR_PROMPT_TEMPLATE = "config/prompts/schema_validator.txt"
DEFAULT_YAML_TEMPLATE = "config/templates/default.yaml"
FIELD_SCORING_PROMPT_TEMPLATE = "config/prompts/field_score_prompt.txt"


# Schema Keywords
SCHEMA_KEYWORDS = ['schema', 'table', 'database', 'dataset']

# Template Placeholders
DATASET_NAME_PLACEHOLDER = "{dataset_name}"
DATASET_DESCRIPTION_PLACEHOLDER = "{dataset_description}"
COLUMN_DESCRIPTIONS_PLACEHOLDER = "{column_descriptions}"
SPECIAL_NOTES_PLACEHOLDER = "{special_notes}"

# Required Fields
REQUIRED_ROLE = "system"
DATASET_DESCRIPTION_HEADER = "[Dataset Description]:"
DATA_ACCESS_STATEMENT = "You can access the entire dataset via the \"data\" variable." 