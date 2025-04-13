"""
OpenAI client for processing PDF content.
"""
import os
from typing import Dict, List, Optional, Tuple
import yaml
from pathlib import Path
from openai import OpenAI

from config.constants import (
    OPENAI_MODEL,
    OPENAI_TEMPERATURE,
    OPENAI_API_KEY,
    DEFAULT_PROMPT_TEMPLATE,
    DEFAULT_SCHEMA_VALIDATOR_PROMPT_TEMPLATE,
)

class OpenAIClientError(Exception):
    """Base exception for OpenAI client errors."""
    pass

class ConfigurationError(OpenAIClientError):
    """Exception raised for configuration errors."""
    pass

class TemplateError(OpenAIClientError):
    """Exception raised for template errors."""
    pass

class OpenAIClient:
    """Client for interacting with OpenAI API."""
    
    def __init__(self):
        """Initialize the OpenAI client with API key and prompt template."""

        # Set API key in environment
        os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

        # Load prompt template
        self.prompt_template, self.schema_validator_prompt_template = self._load_prompt_template()

        # Initialize OpenAI client

        self.client = OpenAI()

    def _load_prompt_template(self) -> str:
        """
        Load the prompt template from file.
        
        Returns:
            The prompt template string
            
        Raises:
            TemplateError: If template file cannot be loaded
        """
        template_path = Path(DEFAULT_PROMPT_TEMPLATE)
        schema_validator_template_path = Path(DEFAULT_SCHEMA_VALIDATOR_PROMPT_TEMPLATE)
        try:
            template = ""
            schema_validator_template = ""
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read().strip()
                if not template or template == "":
                    raise TemplateError("Prompt template file is empty")

            with open(schema_validator_template_path, 'r', encoding='utf-8') as f:
                schema_validator_template = f.read().strip()
                if not schema_validator_template or schema_validator_template == "":
                    raise TemplateError("Schema validator prompt template file is empty")

            return template, schema_validator_template
        except FileNotFoundError:
            raise TemplateError(
                f"Prompt template not found at {template_path} or {schema_validator_template_path}"
            )
        except Exception as e:
            raise TemplateError(f"Error loading prompt template: {e}")

    def gpt_inference(self, text: str, is_for_validation: bool = False, generated_schema: str = "") -> Dict[str, List[Dict[str, str]]]:
        """
        Do the gpt inference. 
        If is_for_validation is false, we will process PDF text content using OpenAI.
        If is_for_validation is true, we will let GPT to validate the generated schema and correct it if it is necessary.
        
        Args:
            text: Raw text extracted from PDF
            
        Returns:
            Dictionary containing dataset descriptions
            
        Raises:
            OpenAIClientError: If processing fails
        """
        try:
            # Create chat completion
            if (is_for_validation == True):
                response = self.client.chat.completions.create(
                    model=OPENAI_MODEL,
                    temperature=OPENAI_TEMPERATURE,
                    messages=[
                        {"role": "system", "content": self.schema_validator_prompt_template},
                        {"role": "user", "content": f"Here is database schema descriptions: {text}"},
                        {"role": "user", "content": f"Here is generated schema: {generated_schema}"}
                    ]
                )
            else:
                response = self.client.chat.completions.create(
                    model=OPENAI_MODEL,
                    temperature=OPENAI_TEMPERATURE,
                    messages=[
                        {"role": "system", "content": self.prompt_template},
                        {"role": "user", "content": text}
                    ]
                )
            
            # Parse response
            content = response.choices[0].message.content
            try:
                # Remove YAML code block markers if present
                if content.startswith('```yaml'):
                    content = content[7:]
                if content.endswith('```'):
                    content = content[:-3]
                content = content.strip()
                
                # Parse YAML content
                result = yaml.safe_load(content)
                if not isinstance(result, dict):
                    raise OpenAIClientError("OpenAI response is not in the expected format")
                return result
            except yaml.YAMLError as e:
                raise OpenAIClientError(f"Failed to parse OpenAI response as YAML: {e}")
            
        except Exception as e:
            raise OpenAIClientError(f"OpenAI API error: {e}") 