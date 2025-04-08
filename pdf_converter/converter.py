from pathlib import Path
from typing import Dict, Tuple, Any
import copy
import re
import yaml  # For YAML parsing

# Import modules for PDF extraction, OpenAI integration, and YAML generation.
from pdf_extractor.extractor import PDFTextExtractor
from openai_integration.client import OpenAIClient, OpenAIClientError
from output_generator.yaml_generator import YAMLGenerator, YAMLGeneratorError


def get_confidence(feature_text: str, openai_client: OpenAIClient, model: str = "gpt-4",
                   temperature: float = 0.0) -> int:
    """
    Evaluate a single feature definition's clarity and correctness using a secondary LLM prompt.

    The LLM is prompted to return a number (0–100) representing the confidence that the feature definition
    (column name, type, and description) is correct and complete.

    Args:
        feature_text: The feature definition line.
        openai_client: An instance of OpenAIClient.
        model: The model to use (default "gpt-4").
        temperature: Temperature setting (default 0.0).

    Returns:
        An integer score between 0 and 100. On error, returns 0.
    """
    prompt = f"""
You are evaluating the clarity and correctness of dataset feature definitions.
For the following line, rate your confidence (from 0 to 100) that the column name, type, and description are all correct and complete.

Only respond with a number from 0 to 100. No explanation.

Line:
{feature_text}
"""
    try:
        response = openai_client.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt.strip()}],
            temperature=temperature,
            max_tokens=5
        )
        score_text = response.choices[0].message.content.strip()
        score = int(score_text)
        return max(0, min(score, 100))
    except Exception as e:
        # Log warning only
        print(f"[LLM Confidence Scoring Warning] {e}")
        return 0


def evaluate_yaml_with_llm(yaml_path: str, openai_client: OpenAIClient) -> float:
    """
    Evaluate the YAML output quality by computing per-feature confidence scores and averaging them.

    Process:
      1. Read and parse the YAML file.
      2. Extract the system entry (role: "system") from the top-level dataset.
      3. For each line matching a feature definition (using regex), call get_confidence.
      4. Average the scores and normalize to a 0–1 scale.

    Returns:
        A composite confidence score (float between 0 and 1). Defaults to 0.0 on failure.
    """
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            yaml_content = f.read().strip()
    except Exception:
        return 0.0

    try:
        parsed = yaml.safe_load(yaml_content)
    except Exception:
        return 0.0

    if not isinstance(parsed, dict) or not parsed:
        return 0.0

    dataset_name = next(iter(parsed.keys()))
    system_entries = parsed.get(dataset_name)
    if not isinstance(system_entries, list) or not system_entries:
        return 0.0

    system_content = None
    for entry in system_entries:
        if entry.get("role") == "system" and "content" in entry:
            system_content = entry["content"]
            break
    if system_content is None:
        return 0.0

    pattern = r'^\s*"([^"]+)"\s*:\s*([^,]+),(.*)$'
    scores = []
    for line in system_content.splitlines():
        m = re.match(pattern, line)
        if m:
            feature_line = f'"{m.group(1).strip()}": {m.group(2).strip()}, {m.group(3).strip()}'
            score = get_confidence(feature_line, openai_client)
            scores.append(score)
    if scores:
        avg_score = sum(scores) / len(scores)
        return avg_score / 100.0
    return 0.0


def transform_yaml_to_json(yaml_path: str, confidence: float, yaml_download_url: str) -> Dict[str, Any]:
    """
    Transform the generated YAML content into a pure JSON object following the required structure.

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
        "yaml_download_path": "{yaml_download_url}",
        "overall_confidence": {overall_confidence},
        "stdout": "",
        "stderr": "",
        "return_code": 0
      }

    This function:
      1. Reads the YAML file.
      2. Assumes a single top-level key representing the dataset name.
      3. Finds the first system entry with a "content" key.
      4. Uses a regex to extract feature definitions.
      5. Constructs and returns the pure JSON object.
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

    pattern = r'^\s*"([^"]+)"\s*:\s*([^,]+),(.*)$'
    fields = []
    for line in system_content.splitlines():
        m = re.match(pattern, line)
        if m:
            fields.append({
                "name": m.group(1).strip(),
                "type": m.group(2).strip(),
                "description": m.group(3).strip(),
                "confidence_score": round(confidence * 100, 2)
            })
    json_obj = {
        "tables": [
            {
                "name": dataset_name,
                "fields": fields
            }
        ],
        "yaml_download_path": yaml_download_url,
        "overall_confidence": round(confidence * 100, 2),
        "stdout": "",
        "stderr": "",
        "return_code": 0
    }
    return json_obj


class PDFConverter:
    def __init__(self, template_path: str, verbose: bool = False):
        """
        Initialize the PDF converter with a YAML template path.

        Args:
            template_path: Path to the YAML template file.
            verbose: Enable verbose logging.
        """
        self.template_path = Path(template_path).resolve()
        self._validate_template()

    def _validate_template(self):
        """Ensure that the YAML template file exists."""
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template file not found: {self.template_path}")

    def convert_pdf(self, pdf_path: str) -> Tuple[str, Dict]:
        """
        Convert a PDF file to YAML and return the YAML download path and pure JSON response.

        Process:
          1. Extract text from the PDF using PDFTextExtractor.
          2. Process the extracted text using OpenAIClient.
          3. Generate YAML output using YAMLGenerator (without confidence scores).
          4. Evaluate the YAML output to compute a composite confidence score.
          5. Transform the YAML output into a pure JSON object.
          6. Return the YAML download path and the JSON response.

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
                    "confidence_score": {confidence_score}
                  },
                  ...
                ]
              }
            ],
            "yaml_download_path": "{path_to_yaml_file}",
            "overall_confidence": {overall_confidence},
            "stdout": "",
            "stderr": "",
            "return_code": 0
          }

        Args:
            pdf_path: Path to the input PDF file.

        Returns:
            A tuple containing:
              - YAML output path (string)
              - JSON response (dict)
        """
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

        # Step 4: Evaluate the YAML output quality.
        confidence_score = evaluate_yaml_with_llm(str(output_path), ai_client)

        # Step 5: Transform the YAML output into the pure JSON response.
        json_response = transform_yaml_to_json(str(output_path), confidence_score, str(output_path))
        return str(output_path), json_response
