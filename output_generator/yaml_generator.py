from pathlib import Path
from typing import Dict, Any
import yaml

class YAMLGeneratorError(Exception):
    """Base exception for YAML generator errors."""
    pass

class YAMLGenerator:
    """Generator for creating YAML output based on templates."""
    
    def __init__(self, template_path: Path):
        self.template = self._load_template(template_path)

    def _load_template(self, template_path: Path) -> Dict[str, Any]:
        """Load and parse the YAML template."""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = yaml.safe_load(f)
                if not template:
                    raise YAMLGeneratorError("Template file is empty")
                return template
        except yaml.YAMLError as e:
            raise YAMLGeneratorError(f"Invalid YAML in template: {e}")
        except Exception as e:
            raise YAMLGeneratorError(f"Error loading template: {e}")

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

    def save(self, content: Dict[str, Any], input_pdf_path: Path) -> Path:
        """
        Generate and save YAML output to a file in the /output directory.
        
        Args:
            content: Dictionary containing dataset descriptions
            input_pdf_path: Path to the input PDF file
            
        Returns:
            Path to the generated YAML file
            
        Raises:
            YAMLGeneratorError: If file cannot be written
        """
        # Generate the YAML content
        yaml_content = self.generate(content)
        
        # Create output directory at project root
        output_dir = Path.cwd() / 'output'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine output path
        pdf_name = input_pdf_path.stem
        output_filename = f"dataset_descriptions_from_{pdf_name}.yaml"
        output_path = output_dir / output_filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
            return output_path
        except Exception as e:
            raise YAMLGeneratorError(f"Error writing YAML file: {e}") 