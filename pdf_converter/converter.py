from pathlib import Path
import logging
from typing import Dict, Tuple, Any
import copy
import re
import yaml  # For YAML parsing

# Import modules for PDF extraction, OpenAI integration, and YAML generation.
from pdf_extractor.extractor import PDFTextExtractor
from openai_integration.client import OpenAIClient, OpenAIClientError
from output_generator.yaml_generator import YAMLGenerator, YAMLGeneratorError


def evaluate_yaml_confidence(yaml_path: str, openai_client: OpenAIClient) -> float:
    """
    Evaluate the quality of the YAML output using a secondary LLM prompt.
    If the LLM evaluation fails, fall back to a simple schema validation.

    The secondary prompt asks the LLM to return a single numerical score (0-1)
    that represents the quality of the YAML output with respect to correctness and completeness.

    Returns:
        A confidence score between 0 and 1.
    """
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            yaml_content = f.read().strip()
    except Exception:
        return 0.0

    prompt = (
        "Evaluate the following YAML content for correctness and completeness in describing a dataset schema. "
        "Respond with only a single numerical value between 0 and 1, where 1 indicates perfect quality and 0 indicates unacceptable quality.\n\n"
        f"YAML Content:\n{yaml_content}"
    )
    try:
        # Assume the OpenAIClient provides a method evaluate_prompt() which returns a score as string.
        response = openai_client.evaluate_prompt(prompt)
        score = float(response.strip())
        return max(0.0, min(1.0, score))
    except Exception:
        # Fallback: simple schema validation.
        try:
            parsed = yaml.safe_load(yaml_content)
            # Check that parsed content is a dict with a non-empty "tables" key.
            if isinstance(parsed, dict) and "tables" in parsed and isinstance(parsed["tables"], list) and parsed[
                "tables"]:
                # For each table, check that each field contains "name", "type", and "description"
                valid = True
                for table in parsed["tables"]:
                    if "fields" not in table or not isinstance(table["fields"], list) or not table["fields"]:
                        valid = False
                        break
                    for field in table["fields"]:
                        if not all(k in field for k in ["name", "type", "description"]):
                            valid = False
                            break
                    if not valid:
                        break
                return 1.0 if valid else 0.0
            else:
                return 0.0
        except Exception:
            return 0.0


def transform_yaml_to_json(yaml_path: str, confidence: float, yaml_download_url: str) -> Dict[str, Any]:
    """
    Transform the generated YAML content into a JSON object with the required structure.

    Expected JSON format:
      {
        "tables": [
          {
            "name": "{dataset_name}",
            "fields": [
              {
                "name": "{column_name}",
                "type": "{column_type}",
                "description": "{column_description}",
                "confidence_score": {confidence}
              },
              ...
            ]
          }
        ],
        "yaml_download_url": "{yaml_download_url}"
      }

    This function:
      1. Reads the YAML file.
      2. Assumes the YAML has a single top-level key representing the dataset name.
      3. Finds the first system entry with a "content" key.
      4. Uses a regex to extract column definitions from the system content.
      5. Builds the JSON object and assigns the provided confidence score to each field.
    """
    with open(yaml_path, "r", encoding="utf-8") as f:
        yaml_content = f.read().strip()
    parsed = yaml.safe_load(yaml_content)
    if not isinstance(parsed, dict) or not parsed:
        raise ValueError("Invalid YAML content: expected a top-level mapping with the dataset name.")

    dataset_name = next(iter(parsed.keys()))
    system_entries = parsed[dataset_name]
    if not isinstance(system_entries, list) or not system_entries:
        raise ValueError("Invalid YAML content: expected a list of system entries under the dataset name.")

    system_content = None
    for entry in system_entries:
        if entry.get("role") == "system" and "content" in entry:
            system_content = entry["content"]
            break
    if system_content is None:
        raise ValueError("Could not find a system entry with content in the YAML.")

    # Use regex to extract lines that start with a quoted column name.
    pattern = r'^\s*"([^"]+)"\s*:\s*([^,]+),(.*)$'
    fields = []
    for line in system_content.splitlines():
        m = re.match(pattern, line)
        if m:
            col_name = m.group(1).strip()
            col_type = m.group(2).strip()
            col_desc = m.group(3).strip()
            fields.append({
                "name": col_name,
                "type": col_type,
                "description": col_desc,
                "confidence_score": confidence
            })
    return {
        "tables": [
            {
                "name": dataset_name,
                "fields": fields
            }
        ],
        "yaml_download_url": yaml_download_url
    }


class PDFConverter:
    def __init__(self, template_path: str, verbose: bool = False):
        """
        Initialize the PDF converter with a template path.
        
        Args:
            template_path: Path to the YAML template file
            verbose: Enable verbose logging
        """
        self.logger = self._setup_logging(verbose)
        self.template_path = Path(template_path).resolve()
        self._validate_template()

    def _setup_logging(self, verbose: bool) -> logging.Logger:
        """Set up logging configuration."""
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(level=level, format='%(message)s')
        return logging.getLogger(__name__)

    def _validate_template(self):
        """Validate that the template file exists."""
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template file not found: {self.template_path}")
        self.logger.debug(f"Template file found: {self.template_path}")

    def convert_pdf(self, pdf_path: str) -> Tuple[str, Dict]:
        """
        Convert a PDF file to YAML and return the download URL and JSON response.

        Args:
            pdf_path: Path to the input PDF file

        Returns:
            Tuple containing:
            - YAML file download URL
            - JSON response following the API specification
        """
        self.logger.info(f"Starting conversion for PDF: {pdf_path}")
        pdf_path_obj = Path(pdf_path).resolve()
        if not pdf_path_obj.exists():
            raise FileNotFoundError(f"Input PDF file not found: {pdf_path_obj}")

        # Step 1: Extract PDF text.
        extractor = PDFTextExtractor(str(pdf_path_obj))
        raw_text = extractor.extract_text()
        if not raw_text.strip():
            raise ValueError("No text could be extracted from the PDF.")

        # Step 2: Process text with OpenAIClient.
        ai_client = OpenAIClient()
        processed_content = ai_client.process_pdf_text(raw_text)

        # Step 3: Generate YAML output.
        content_for_yaml = copy.deepcopy(processed_content)
        for table in content_for_yaml.get("tables", []):
            for field in table.get("fields", []):
                field.pop("confidence_score", None)
        generator = YAMLGenerator(self.template_path)
        output_path = generator.save(content_for_yaml, pdf_path_obj)
        self.logger.info(f"YAML output written to: {output_path}")

        # Step 4: Evaluate the YAML output quality.
        confidence_score = evaluate_yaml_confidence(str(output_path), ai_client)
        self.logger.info(f"Evaluated YAML output confidence: {confidence_score:.2f}")

        # Step 5: Transform the YAML output into the JSON response.
        json_response = transform_yaml_to_json(str(output_path), confidence_score, str(output_path))

        self.logger.info("PDF conversion completed successfully.")
        return str(output_path), json_response
