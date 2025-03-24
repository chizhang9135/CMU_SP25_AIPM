from typing import Dict, List, Any, Optional, Tuple
import os
from pathlib import Path
import yaml
from openai import OpenAI
from config.constants import (
    OPENAI_API_KEY_ENV,
    OPENAI_MODEL,
    OPENAI_TEMPERATURE,
    DEFAULT_PROMPT_TEMPLATE,
    SCHEMA_KEYWORDS,
    REQUIRED_ROLE,
)

class OpenAIClient:
    """Client for processing structured content using OpenAI."""
    
    def __init__(self, prompt_template_path: str = DEFAULT_PROMPT_TEMPLATE):
        self.client = OpenAI(api_key=os.getenv(OPENAI_API_KEY_ENV))
        self.system_prompt = self._load_prompt_template(prompt_template_path)

    def _load_prompt_template(self, template_path: str) -> str:
        """Load the prompt template from file."""
        try:
            with open(template_path, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Prompt template not found at {template_path}. "
                "Please ensure the template file exists in the config/prompts directory."
            )

    def process_content(self, structured_content: Dict[str, Any]) -> Dict[str, List[Dict[str, str]]]:
        """
        Process structured content into dataset descriptions.
        
        Args:
            structured_content: Dictionary containing structured content from the PDF
            
        Returns:
            Dictionary containing dataset descriptions in the required format
        """
        # Extract relevant sections that contain schema information
        schemas = self._identify_schemas(structured_content)
        
        # Process each schema
        datasets = {}
        for schema in schemas:
            response = self._generate_dataset_description(schema)
            if response:
                dataset_name, description = response
                datasets[dataset_name] = description
        
        return datasets

    def _identify_schemas(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract schema definitions from the structured content."""
        schemas = []
        
        # Look for schema definitions in sections
        for section in content.get('sections', []):
            if any(keyword in section['title'].lower() 
                  for keyword in SCHEMA_KEYWORDS):
                schemas.append({
                    'title': section['title'],
                    'content': section['content'],
                    'tables': self._find_related_tables(content.get('tables', []), section),
                })
        
        return schemas

    def _find_related_tables(self, tables: List[Dict[str, Any]], section: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find tables that are related to this schema section."""
        # Simple heuristic: tables that appear within the section's content
        section_content = '\n'.join(section['content'])
        return [table for table in tables 
                if any(col in section_content for col in table['headers'])]

    def _generate_dataset_description(self, schema: Dict[str, Any]) -> Optional[Tuple[str, List[Dict[str, str]]]]:
        """
        Generate a dataset description for a schema using OpenAI.
        
        Args:
            schema: Dictionary containing schema information
            
        Returns:
            Tuple of (dataset_name, description) if successful, None if parsing fails
        """
        # Prepare the schema content for the prompt
        schema_content = f"""
        Title: {schema['title']}
        
        Content:
        {'\n'.join(schema['content'])}
        
        Tables:
        {self._format_tables(schema['tables'])}
        """
        
        # Call OpenAI API
        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": REQUIRED_ROLE, "content": self.system_prompt},
                {"role": "user", "content": f"Convert this schema into a dataset description:\n{schema_content}"}
            ],
            temperature=OPENAI_TEMPERATURE,
        )
        
        # Extract dataset name and description from the response
        try:
            response_text = response.choices[0].message.content
            # Parse the YAML-formatted response
            dataset = yaml.safe_load(response_text)
            name = next(iter(dataset.keys()))
            return name, dataset[name]
        except Exception as e:
            print(f"Error parsing OpenAI response: {e}")
            return None

    def _format_tables(self, tables: List[Dict[str, Any]]) -> str:
        """Format tables for inclusion in the prompt."""
        result = []
        for table in tables:
            headers = ' | '.join(table['headers'])
            result.append(f"Headers: {headers}")
            for row in table['rows']:
                result.append(' | '.join(row))
        return '\n'.join(result) 