from pathlib import Path
from typing import Dict, Tuple, Any, List
import copy
import re
import yaml  # For YAML parsing
import json  # For JSON conversion if needed

# Import modules for PDF extraction, OpenAI integration, and YAML generation.
from pdf_extractor.extractor import PDFTextExtractor
from openai_integration.client import OpenAIClient, OpenAIClientError
from output_generator.yaml_generator import YAMLGenerator, YAMLGeneratorError


def get_confidence(feature_text: str, openai_client: OpenAIClient, model: str = "gpt-4",
                   temperature: float = 0.0) -> int:
    """
    Use a secondary LLM prompt to evaluate a single feature definition.

    The prompt now provides additional context so the LLM evaluates clarity,
    correctness, and completeness of the feature definition.

    Args:
        feature_text: The complete feature definition line.
        openai_client: An instance of OpenAIClient.
        model: Model to use (default "gpt-4").
        temperature: Temperature setting (default 0.0).

    Returns:
        An integer confidence score between 0 and 100. On failure, returns 0.
    """
    refined_prompt = f"""
You are an expert in dataset schema quality.
Review the following feature definition:
{feature_text}

Evaluate its clarity, correctness, and completeness.
Return your confidence score as a number between 0 and 100, where 100 indicates perfect quality.
Only reply with the number and nothing else.
"""
    try:
        response = openai_client.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": refined_prompt.strip()}],
            temperature=temperature,
            max_tokens=5
        )
        score_text = response.choices[0].message.content.strip()
        score = int(score_text)
        return max(0, min(score, 100))
    except Exception as e:
        print(f"[LLM Confidence Scoring Warning] {e}")
        return 0


def extract_features(system_content: str) -> List[Dict[str, Any]]:
    """
    Extract all feature definition lines from the system content using re.findall.

    Expected format (each line):
      "column_name": column_type, description

    Returns:
        A list of dictionaries for each feature with keys:
        'name', 'type', 'description', and 'feature_line'.
    """
    pattern = r'^\s*"([^"]+)"\s*:\s*([^,]+),\s*(.+)$'
    matches = re.findall(pattern, system_content, re.MULTILINE)
    features = []
    for match in matches:
        feature_line = f'"{match[0].strip()}": {match[1].strip()}, {match[2].strip()}'
        features.append({
            "name": match[0].strip(),
            "type": match[1].strip(),
            "description": match[2].strip(),
            "feature_line": feature_line
        })
    return features


def evaluate_yaml_with_llm(yaml_path: str, openai_client: OpenAIClient) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Evaluate the YAML output quality by computing individual confidence scores
    for each feature and averaging them.

    Process:
      1. Read and parse the YAML file.
      2. Extract the system content (from the first system entry under the top-level key).
      3. Use extract_features() to get all feature definitions.
      4. For each feature, call get_confidence to obtain an individual score.
      5. Compute the overall confidence as the average (normalized to 0–1).

    Returns:
        A tuple (overall_confidence, features) where overall_confidence is a float (0–1),
        and features is the list of feature dictionaries including their individual scores.
    """
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            yaml_content = f.read().strip()
    except Exception:
        return 0.0, []

    try:
        parsed = yaml.safe_load(yaml_content)
    except Exception:
        return 0.0, []

    if not isinstance(parsed, dict) or not parsed:
        return 0.0, []

    dataset_name = next(iter(parsed.keys()))
    system_entries = parsed.get(dataset_name)
    if not isinstance(system_entries, list) or not system_entries:
        return 0.0, []

    system_content = None
    for entry in system_entries:
        if entry.get("role") == "system" and "content" in entry:
            system_content = entry["content"]
            break
    if system_content is None:
        return 0.0, []

    features = extract_features(system_content)
    if not features:
        return 0.0, []

    total_score = 0
    for feature in features:
        score = get_confidence(feature["feature_line"], openai_client)
        feature["confidence_score"] = score
        total_score += score

    overall_confidence = (total_score / len(features)) / 100.0
    return overall_confidence, features


def transform_yaml_to_json(yaml_path: str, overall_confidence: float, features: List[Dict[str, Any]],
                           yaml_download_url: str) -> Dict[str, Any]:
    """
    Transform the generated YAML content into a pure JSON object following the required schema.

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
        "yaml_download_path": "{yaml_download_url}",
        "overall_confidence": {overall_confidence},
        "stdout": "",
        "stderr": "",
        "return_code": 0
      }

    Here, the features list (with their individual scores computed above) is used directly.
    """
    with open(yaml_path, "r", encoding="utf-8") as f:
        yaml_content = f.read().strip()
    parsed = yaml.safe_load(yaml_content)
    if not isinstance(parsed, dict) or not parsed:
        raise ValueError("Invalid YAML content: expected a top-level mapping with the dataset name.")

    dataset_name = next(iter(parsed.keys()))
    json_obj = {
        "tables": [
            {
                "name": dataset_name,
                "fields": [
                    {
                        "name": feat["name"],
                        "type": feat["type"],
                        "description": feat["description"],
                        "confidence_score": feat["confidence_score"]
                    }
                    for feat in features
                ]
            }
        ],
        "yaml_download_path": yaml_download_url,
        "overall_confidence": round(overall_confidence * 100, 2),
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
            verbose: Enable verbose logging (default: minimal logging).
        """
        self.template_path = Path(template_path).resolve()
        self._validate_template()

    def _validate_template(self):
        """Ensure that the YAML template file exists."""
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template file not found: {self.template_path}")

    def convert_pdf(self, pdf_path: str) -> Tuple[str, Dict]:
        """
        Convert a PDF file to YAML and return the YAML download path and a pure JSON response.

        Process:
          1. Extract text from the PDF using PDFTextExtractor.
          2. Process the extracted text using OpenAIClient.
          3. Generate YAML output using YAMLGenerator (without confidence scores).
          4. Evaluate the YAML output to compute individual feature confidence scores.
          5. Compute an overall confidence score.
          6. Transform the YAML output into a pure JSON object.
          7. Return the YAML download path and the JSON object.

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

        # Step 3: Generate YAML output (remove any pre-existing confidence scores).
        content_for_yaml = copy.deepcopy(processed_content)
        for table in content_for_yaml.get("tables", []):
            for field in table.get("fields", []):
                field.pop("confidence_score", None)
        generator = YAMLGenerator(self.template_path)
        output_path = generator.save(content_for_yaml, pdf_path_obj)

        # Step 4: Evaluate the YAML output quality (per-feature confidence scores).
        overall_confidence, features = evaluate_yaml_with_llm(str(output_path), ai_client)

        # Step 5: Transform the YAML output into a pure JSON object.
        json_obj = transform_yaml_to_json(str(output_path), overall_confidence, features, str(output_path))
        return str(output_path), json_obj
