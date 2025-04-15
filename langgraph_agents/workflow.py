# Standard library imports
import copy
import json
import re
import traceback
from pathlib import Path
from typing import Any, Dict, List, Literal, Tuple

# Third-party imports
import yaml
from langgraph.graph import END, START, StateGraph

# Local application imports
from langgraph_agents.agents.validator import SchemaValidator
from langgraph_agents.states import PDFState, WorkflowConfig
from openai_integration.client import OpenAIClient
from output_generator.yaml_generator import YAMLGenerator
from pdf_extractor.extractor import PDFTextExtractor

class PDFToYAMLWorkflow:
    """Main workflow for PDF to YAML conversion with validation"""
    
    def __init__(self, template_path: str = "config/templates/default.yaml"):
        self.config = WorkflowConfig(max_iterations=3, confidence_threshold=0.8)
        self.openai_client = OpenAIClient()
        self.yaml_generator = YAMLGenerator(template_path)
        self.validator = SchemaValidator(self.config)
        self.graph = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Creates the workflow graph with all nodes and edges"""
        print("Creating workflow")
        graph = StateGraph(PDFState)
        
        # Add nodes
        graph.add_node("extract", self._extract_text)
        graph.add_node("generate", self._generate_yaml)
        graph.add_node("validate", self._validate_yaml)
        graph.add_node("output", self._format_output)
        
        # Add edges
        graph.add_edge(START, "extract")
        graph.add_edge("extract", "generate")
        graph.add_edge("generate", "validate")
        
        # Add conditional edges with proper edge condition functions
        # def validate_router(state: Dict) -> str:
        #     if state.get("is_final"):
        #         if state.get("confidence_score", 0) >= self.config.confidence_threshold:
        #             return "output"
        #         return "output"  # force output even with low confidence
        #     return "generate"  # retry generation

        def validate_router(state: Dict) -> str:
            feedback = state.get("validation_feedback") or ""
            if any(tag in feedback for tag in ["[NAME GATE]", "[TYPE GATE]", "[DESC GATE]", "[STRUCTURE]"]):
                if state.get("iteration_count", 0) < self.config.max_iterations:
                    return "generate"
            return "output"

        graph.add_conditional_edges("validate", validate_router)
        graph.add_edge("output", END)
        
        return graph.compile()
    
    async def _extract_text(self, state: PDFState) -> PDFState:
        """Extracts text from PDF"""
        print("Extracting text")
        try:
            print(f"Extracting text from {state}")
            extractor = PDFTextExtractor(state["pdf_path"])
            state["extracted_text"] = extractor.extract_text()
            return state
        except Exception as e:
            print(f"Error extracting text: {str(e)}")
            state["error"] = str(e)
            state["stacktrace"] = traceback.format_exc()
            state["is_final"] = True
            return state
    
    async def _generate_yaml(self, state: PDFState) -> PDFState:
        """Generates YAML using OpenAI"""
        print("Generating YAML")
        try:
            prompt = self._create_prompt(state)
            state["current_yaml"] = self.openai_client.gpt_inference(prompt)
            state["iteration_count"] = state.get("iteration_count", 0) + 1
            return state
        except Exception as e:
            state["error"] = str(e)
            state["stacktrace"] = traceback.format_exc()
            state["is_final"] = True
            return state

    async def _validate_yaml(self, state: PDFState) -> PDFState:
        """Validates YAML and determines next step"""
        print("Validating YAML")
        try:
            # Ensure previous values are properly tracked
            if "failed_fields" not in state:
                state["failed_fields"] = []

            if "field_positions" not in state:
                state["field_positions"] = {}

            # Validate YAML
            validated_state = await self.validator.validate_and_suggest(state)

            # Update state with validation results
            for key in ["confidence_score", "validation_feedback", "failed_fields", "field_positions", "is_final"]:
                if key in validated_state:
                    state[key] = validated_state[key]

            print(
                f"[WORKFLOW] Validation complete - confidence: {state['confidence_score']}, failed fields: {len(state.get('failed_fields', []))}")
            return state

        except Exception as e:
            print(f"Error in validation: {str(e)}")
            state["error"] = str(e)
            state["stacktrace"] = traceback.format_exc()
            state["is_final"] = True
            return state
    
    # async def _validate_yaml(self, state: PDFState) -> PDFState:
    # Comment for improvement
    #     """Validates YAML and determines next step"""
    #     print("Validating YAML")
    #     try:
    #         validated_state = await self.validator.validate_and_suggest(state)
    #         # Update the current state with validation results
    #         state.update(validated_state)
    #
    #         # Set is_final if we've hit max iterations or have high confidence
    #         if (state.get("iteration_count", 0) >= self.config.max_iterations or
    #             state.get("confidence_score", 0) >= self.config.confidence_threshold):
    #             state["is_final"] = True
    #
    #         return state
    #     except Exception as e:
    #         state["error"] = str(e)
    #         state["stacktrace"] = traceback.format_exc()
    #         state["is_final"] = True
    #         return state
    
    async def _format_output(self, state: PDFState) -> PDFState:
        """Formats the final YAML output"""
        print("Formatting output")
        try:
            if not state.get("error") and state.get("current_yaml"):
                content_for_yaml = copy.deepcopy(state["current_yaml"])
                for table in content_for_yaml.get("tables", []):
                    for field in table.get("fields", []):
                        field.pop("confidence_score", None)
                pdf_path_obj = Path(state["pdf_path"]).resolve()
                output_path = self.yaml_generator.save(content_for_yaml, pdf_path_obj)
                print(f"Output written to: {output_path}")
                features = self._evaluate_yaml_with_llm(str(output_path))
                json_obj = self._transform_yaml_to_json(str(output_path), features, str(output_path))
                state["output_path"] = output_path
                state["json_obj"] = json_obj
            return state
        except Exception as e:
            state["error"] = str(e)
            state["stacktrace"] = traceback.format_exc()
            state["is_final"] = True
            return state
    
    # def _create_prompt(self, state: PDFState) -> str:
    #     Comment for improvement
    #     """Creates prompt for OpenAI based on state"""
    #     prompt = f"Convert this text to YAML:\n{state['extracted_text']}"
    #
    #     if state.get("current_yaml"):
    #         prompt += f"\n\nHere is the previous generated YAML:\n{state['current_yaml']}"
    #     if state.get("validation_feedback"):
    #         prompt += f"\n\nPrevious validation feedback:\n{state['validation_feedback']}"
    #     return prompt

    def _create_prompt(self, state: PDFState) -> str:
        """Creates optimized prompt for OpenAI based on state"""
        prompt = f"Convert the following text to a YAML schema:\n\n{state['extracted_text']}\n\n"

        if state.get("current_yaml"):
            prompt += "\nPrevious YAML schema:\n---\n"
            prompt += yaml.dump(state["current_yaml"], sort_keys=False)
            prompt += "\n---\n"

        if state.get("validation_feedback"):
            prompt += f"\nValidator Feedback:\n{state['validation_feedback']}\n"

        failed_fields = state.get("failed_fields", [])

        # Create more targeted instructions
        if failed_fields:
            failed_str = ", ".join(f'"{f}"' for f in failed_fields)

            # More specific instructions that encourage better field naming
            prompt += (
                f"\nPlease regenerate ONLY the following fields in the YAML schema: {failed_str}.\n"
                f"For each field:\n"
                f"1. Improve the NAME to be more descriptive and specific (scores must be ≥90)\n"
                f"2. Ensure TYPE is appropriate and accurate (scores must be ≥75)\n"
                f"3. Make DESCRIPTIONS clear, specific and complete (scores must be ≥75)\n\n"
                f"IMPORTANT: Keep all other fields EXACTLY as they appear in the previous YAML.\n"
                f"DO NOT modify or rename any fields except those listed above.\n"
            )
        else:
            prompt += "\nGenerate a complete YAML schema with descriptive field names and clear descriptions."

        return prompt

    def _transform_yaml_to_json(self, yaml_path: str, features: List[Dict[str, Any]],
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
                    "description": "{column_description}"
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
                            "description": feat["description"]
                        }
                        for feat in features
                    ]
                }
            ],
            "yaml_download_path": yaml_download_url,
            "stdout": "",
            "stderr": "",
            "return_code": 0
        }
        return json_obj
    
    def _evaluate_yaml_with_llm(self, yaml_path: str) -> Tuple[float, List[Dict[str, Any]]]:
        """
        Evaluate the YAML output quality by computing individual confidence scores
        for each feature and averaging them.

        Process:
        1. Read and parse the YAML file.
        2. Extract the system content (from the first system entry under the top-level key).
        3. Use extract_features() to get all feature definitions.

        Returns:
            features is the list of feature dictionaries including their individual scores.
        """
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                yaml_content = f.read().strip()
        except Exception:
            return 0.0, []

        try:
            parsed = yaml.safe_load(yaml_content)
        except Exception:
            return []

        if not isinstance(parsed, dict) or not parsed:
            return []

        dataset_name = next(iter(parsed.keys()))
        system_entries = parsed.get(dataset_name)
        if not isinstance(system_entries, list) or not system_entries:
            return []

        system_content = None
        for entry in system_entries:
            if entry.get("role") == "system" and "content" in entry:
                system_content = entry["content"]
                break
        if system_content is None:
            return []

        features = self._extract_features(system_content)
        if not features:
            return []

        return features
    
    def _extract_features(self, system_content: str) -> List[Dict[str, Any]]:
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
    
    async def run(self, pdf_path: str) -> PDFState:
        """Runs the workflow on a PDF file"""
        initial_state = {
            "pdf_path": pdf_path,
            "extracted_text": "",
            "current_yaml": None,
            "iteration_count": 0,
            "confidence_score": 0.0,
            "validation_feedback": None,
            "is_final": False,
            "error": None,
            "stacktrace": None,
            # new add
            "failed_fields": [],
            "field_positions": {}
        }

        try:
            final_state = await self.graph.ainvoke(initial_state)
            return final_state
        except Exception as e:
            print(f"Workflow failed with error: {str(e)}")
            initial_state["error"] = str(e)
            initial_state["stacktrace"] = traceback.format_exc()
            initial_state["is_final"] = True
            return initial_state
