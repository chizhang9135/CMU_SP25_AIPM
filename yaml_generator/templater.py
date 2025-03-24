from pathlib import Path
from typing import Dict, Any
import yaml

class YAMLGenerator:
    """Generator for creating YAML output based on templates."""
    
    def __init__(self, template_path: Path):
        self.template = self._load_template(template_path)

    def _load_template(self, template_path: Path) -> Dict[str, Any]:
        """Load and parse the YAML template."""
        with open(template_path) as f:
            return yaml.safe_load(f)

    def generate(self, content: Dict[str, Any]) -> str:
        """
        Generate YAML output based on the template and content.
        
        Args:
            content: Dictionary containing dataset descriptions
            
        Returns:
            Formatted YAML string
        """
        # Format the content according to template
        formatted_content = {}
        
        for dataset_name, dataset_content in content.items():
            # Ensure the content follows the template structure
            if isinstance(dataset_content, list) and len(dataset_content) > 0:
                formatted_content[dataset_name] = dataset_content
        
        # Convert to YAML string
        return yaml.dump(
            formatted_content,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=1000  # Prevent line wrapping in content blocks
        ) 