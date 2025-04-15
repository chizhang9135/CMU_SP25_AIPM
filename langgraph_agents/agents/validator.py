from typing import Dict, Tuple, Optional
from pathlib import Path
from openai_integration.client import OpenAIClient
from langgraph_agents.states import PDFState, WorkflowConfig
import re
from config.constants import OPENAI_MODEL


class SchemaValidator:
    """Validator agent for checking YAML schema and suggesting corrections"""

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.openai_client = OpenAIClient()
        self.field_score_prompt_template = self._load_field_prompt()


    def _load_field_prompt(self) -> str:
        """
        Loads the field-level scoring prompt template.
        """
        prompt_path = Path("config/prompts/field_score_prompt.txt")  # Adjust if your prompt is elsewhere
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            print(f"[SchemaValidator] Failed to load scoring prompt: {e}")
            return ""

    def _load_field_prompt(self) -> str:
        prompt_path = Path("config/prompts/field_score_prompt.txt")
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            print(f"[SchemaValidator] Failed to load scoring prompt: {e}")
            return ""

    async def _score_component(self, field_type: str, field_value: str) -> float:
        if not field_value:
            return 0.0

        prompt = self.field_score_prompt_template.format(
            field_type=field_type,
            field_value=field_value
        )

        try:
            response = self.openai_client.client.chat.completions.create(
                model=OPENAI_MODEL,
                temperature=0,
                messages=[
                    {"role": "system", "content": "You are evaluating the clarity and correctness of dataset feature definitions. For the following {field_type}, rate your confidence (from 0 to 100) based on the rubric. Only respond with a float from 0 to 100. Do not explain or justify the score."},
                    {"role": "user", "content": prompt}
                ]
            )
            content = response.choices[0].message.content.strip()
            print(f"[GPT SCORE RAW] {field_type}: {field_value} → {content}")
            return float(content)

        except Exception as e:
            print(f"[ERROR] GPT scoring failed for {field_type}: {e}")
            return 0.0

    async def validate_and_suggest(
        self,
        state: PDFState
    ) -> PDFState:
        """
        Validates YAML and provides correction suggestions if needed.
        Updates the state with validation results and feedback.

        Args:
            state: Current workflow state

        Returns:
            Updated state with validation results
        """
        print(f"Validating YAML. Iteration count: {state.get('iteration_count', 0)}")
        if state.get("iteration_count", 0) >= self.config.max_iterations:
            state["is_final"] = True
            return state

        # Validate the current YAML
        is_valid, confidence, feedback = await self._check_yaml(state.get("current_yaml"))

        # Update state
        state["confidence_score"] = confidence
        state["validation_feedback"] = feedback
        # Default threshold is 0.8 ~ 80% confidence
        state["is_final"] = is_valid or (confidence >= self.config.confidence_threshold)

        return state

    async def _check_yaml(
        self,
        yaml_content: Dict
    ) -> Tuple[bool, float, Optional[str]]:
        """
        Checks YAML content validity and generates feedback.
        Currently configured to always pass for testing.

        Returns:
            Tuple of (is_valid, confidence_score, feedback)
        """
        # TODO do the confidence logic here
        # ========== STEP 1: Parse YAML structure ==========
        if not yaml_content or len(yaml_content) == 0:
            return False, 0.0, "No YAML content found"

        dataset_name = next(iter(yaml_content))
        entries = yaml_content[dataset_name]

        if not isinstance(entries, list) or len(entries) == 0:
            return False, 0.0, f"No entries under dataset '{dataset_name}'"

        raw_text = entries[0].get("content", "")
        if not raw_text:
            return False, 0.0, "No 'content' found in dataset entry"

        lines = raw_text.splitlines()
        columns = []
        for line in lines:
            match = re.match(r'^"(.*?)":\s*(\w+),\s*(.*)', line.strip())
            if match:
                name, dtype, desc = match.groups()
                columns.append({
                    "name": name.strip(),
                    "type": dtype.strip(),
                    "description": desc.strip()
                })

        if not columns:
            return False, 0.0, "No valid fields found in schema"

        print(f"[VALIDATOR DEBUG] Parsed {len(columns)} fields")

        field_scores = []
        feedback_lines = []
        structure_fail = name_fail = quality_fail = False

        def label(score: float) -> str:
            if score >= 90: return "accurate"
            if score >= 75: return "aligned"
            if score >= 60: return "vague"
            if score >= 40: return "inaccurate"
            return "missing"

        for col in columns:
            fid = col.get("name", "UNKNOWN")
            name = col.get("name", "").strip()
            dtype = col.get("type", "").strip()
            desc = col.get("description", "").strip()

            # Step 1: Structure Gate
            missing = []
            if not name: missing.append("name")
            if not dtype: missing.append("type")
            if not desc: missing.append("description")
            if missing:
                structure_fail = True
                feedback_lines.append(f"[STRUCTURE GATE] '{fid}' missing: {', '.join(missing)}")

            # Step 2: Score fields
            name_score = await self._score_component("name", name)
            type_score = await self._score_component("type", dtype)
            desc_score = await self._score_component("description", desc)

            print(f"[SCORE] {fid} → name: {name_score}, type: {type_score}, desc: {desc_score}")

            field_score = 0.5 * name_score + 0.3 * desc_score + 0.2 * type_score
            field_scores.append(field_score)

            # Step 3: Retry Gates
            if name_score < 90:
                name_fail = True
                feedback_lines.append(f"[NAME GATE] '{fid}' name_score={name_score:.1f} ({label(name_score)})")
            if type_score < 75:
                quality_fail = True
                feedback_lines.append(f"[TYPE GATE] '{fid}' type_score={type_score:.1f} ({label(type_score)})")
            if desc_score < 75:
                quality_fail = True
                feedback_lines.append(f"[DESC GATE] '{fid}' desc_score={desc_score:.1f} ({label(desc_score)})")

        # Step 4: Compute schema-level confidence
        schema_conf = sum(field_scores) / len(field_scores) if field_scores else 0.0
        confidence_score = round(schema_conf / 100.0, 4)

        retry_required = structure_fail or name_fail or quality_fail
        is_valid = not retry_required
        feedback = "\n".join(feedback_lines) if feedback_lines else None

        print(f"[VALIDATOR RESULT] ✅ is_valid: {is_valid} | confidence: {confidence_score:.4f}")
        if feedback:
            print(f"[VALIDATOR RESULT] ❗ Feedback:\n{feedback}")

        return is_valid, confidence_score, feedback
