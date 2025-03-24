"""
OpenAI client for processing PDF content.
"""
import os
from typing import Dict, List, Optional, Tuple
import yaml
from pathlib import Path

from config.constants import (
    OPENAI_API_KEY_ENV,
    OPENAI_MODEL,
    OPENAI_TEMPERATURE,
    DEFAULT_PROMPT_TEMPLATE,
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
        # Set up OpenAI API key
        os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY_ENV
        
        # Load prompt template
        self.prompt_template = self._load_prompt_template()
        
        # Initialize OpenAI client
        import openai
        self.client = openai.OpenAI()

    def _load_prompt_template(self) -> str:
        """
        Load the prompt template from file.
        
        Returns:
            The prompt template string
            
        Raises:
            TemplateError: If template file cannot be loaded
        """
        template_path = Path(DEFAULT_PROMPT_TEMPLATE)
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read().strip()
                if not template:
                    raise TemplateError("Prompt template file is empty")
                return template
        except FileNotFoundError:
            raise TemplateError(
                f"Prompt template not found at {template_path}"
            )
        except Exception as e:
            raise TemplateError(f"Error loading prompt template: {e}")

    def process_pdf_text(self, text: str) -> Dict[str, List[Dict[str, str]]]:
        """
        Process PDF text content using OpenAI.
        
        Args:
            text: Raw text extracted from PDF
            
        Returns:
            Dictionary containing dataset descriptions
            
        Raises:
            OpenAIClientError: If processing fails
        """
        try:
            # Create chat completion
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