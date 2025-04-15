from typing import Dict, Tuple, Optional, List, Set
from pathlib import Path
from openai_integration.client import OpenAIClient
from langgraph_agents.states import PDFState, WorkflowConfig
import re
from config.constants import OPENAI_MODEL
import logging

# Setup logger
logger = logging.getLogger("Validator")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(levelname)s] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class SchemaValidator:
    """Validator agent for checking YAML schema and suggesting corrections"""

    field_scores_cache = {}

    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.openai_client = OpenAIClient()
        self.field_score_prompt_template = self._load_field_prompt()

    def _load_field_prompt(self) -> str:
        prompt_path = Path("config/prompts/field_score_prompt.txt")
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Failed to load scoring prompt: {e}")
            return ""

    async def _score_component(self, field_type: str, field_value: str) -> float:
        if not field_value:
            return 0.0

        cache_key = f"{field_type}:{field_value}"
        if cache_key in self.field_scores_cache:
            return self.field_scores_cache[cache_key]

        prompt = self.field_score_prompt_template.format(
            field_type=field_type,
            field_value=field_value
        )

        try:
            response = self.openai_client.client.chat.completions.create(
                model=OPENAI_MODEL,
                temperature=0,
                messages=[
                    {"role": "system",
                     "content": "You are evaluating the clarity and correctness of dataset feature definitions. For the following {field_type}, rate your confidence (from 0 to 100) based on the rubric. Only respond with a float from 0 to 100. Do not explain or justify the score."},
                    {"role": "user", "content": prompt}
                ]
            )
            content = response.choices[0].message.content.strip()
            score = float(content)

            self.field_scores_cache[cache_key] = score
            return score

        except Exception as e:
            logger.error(f"Scoring failed for {field_type}: {e}")
            return 0.0

    def _label_score(self, score: float) -> str:
        if score >= 90: return "Accurate & Specific"
        if score >= 75: return "Semantically Aligned"
        if score >= 60: return "Vague / Abstract"
        if score >= 40: return "Inaccurate"
        return "Missing or irrelevant"

    async def validate_and_suggest(self, state: PDFState) -> PDFState:
        iteration = state.get("iteration_count", 0)
        logger.info(f"🔍 Starting validation | Iteration {iteration}")

        if iteration >= self.config.max_iterations:
            state["is_final"] = True
            return state

        previous_failed_fields = state.get("failed_fields", [])
        field_positions = state.get("field_positions", {})

        is_valid, confidence, feedback, failed_fields, new_field_positions = await self._check_yaml(
            state.get("current_yaml"), previous_failed_fields, field_positions, iteration
        )

        state["confidence_score"] = confidence
        state["validation_feedback"] = feedback
        state["failed_fields"] = failed_fields
        state["field_positions"] = new_field_positions
        state["is_final"] = (iteration >= self.config.max_iterations or is_valid)

        return state

    async def _check_yaml(
        self,
        yaml_content: Dict,
        previous_failed_fields: List[str] = None,
        previous_field_positions: Dict[str, int] = None,
        iteration: int = 1
    ) -> Tuple[bool, float, Optional[str], List[str], Dict[str, int]]:

        field_scores = []
        feedback_lines = []
        failed_fields = []

        if not yaml_content or len(yaml_content) == 0:
            return False, 0.0, "No YAML content found", [], {}

        dataset_name = next(iter(yaml_content))
        entries = yaml_content[dataset_name]

        if not isinstance(entries, list) or len(entries) == 0:
            return False, 0.0, f"No entries under dataset '{dataset_name}'", [], {}

        raw_text = entries[0].get("content", "")
        if not raw_text:
            return False, 0.0, "No 'content' found in dataset entry", [], {}

        columns = []
        field_positions = {}

        for line in raw_text.splitlines():
            match = re.match(r'^"(.*?)":\s*(\w+),\s*(.*)', line.strip())
            if match:
                name, dtype, desc = match.groups()
                field_id = name.strip()
                columns.append({
                    "name": field_id,
                    "type": dtype.strip(),
                    "description": desc.strip()
                })
                field_positions[field_id] = len(columns) - 1

        if not columns:
            return False, 0.0, "No valid fields found in schema", [], {}

        total_fields = len(columns)
        is_selective = (iteration > 1 and previous_failed_fields)

        fields_to_evaluate = set()
        if is_selective:
            for field_name in previous_failed_fields:
                if field_name in field_positions:
                    fields_to_evaluate.add(field_name)
                elif previous_field_positions and field_name in previous_field_positions:
                    pos = previous_field_positions[field_name]
                    if 0 <= pos < total_fields:
                        fields_to_evaluate.add(columns[pos]["name"])
            logger.info(f"⚙️ Selective validation | Evaluating {len(fields_to_evaluate)} of {total_fields} fields")
        else:
            fields_to_evaluate = {col["name"] for col in columns}
            logger.info(f"📋 Full validation | Evaluating all {total_fields} fields")

        structure_fail = name_fail = quality_fail = False
        evaluated_count = skipped_count = 0

        for col in columns:
            field_id = col["name"]
            name = col["name"].strip()
            dtype = col["type"].strip()
            desc = col["description"].strip()

            if field_id not in fields_to_evaluate:
                field_scores.append(90.0)
                skipped_count += 1
                continue

            evaluated_count += 1

            if not name or not dtype or not desc:
                structure_fail = True
                if not name:
                    feedback_lines.append(f"[STRUCTURE] Field '{field_id}' is missing a name component")
                if not dtype:
                    feedback_lines.append(f"[STRUCTURE] Field '{field_id}' is missing a type component")
                if not desc:
                    feedback_lines.append(f"[STRUCTURE] Field '{field_id}' is missing a description component")
                failed_fields.append(field_id)
                continue

            name_score = await self._score_component("name", name)
            type_score = await self._score_component("type", dtype)
            desc_score = await self._score_component("description", desc)

            field_score = (name_score * 0.5) + (desc_score * 0.3) + (type_score * 0.2)
            field_scores.append(field_score)

            if name_score < 90 or type_score < 75 or desc_score < 75:
                logger.warning(f"🧪 Field: '{field_id}' | name: {name_score:.1f}, type: {type_score:.1f}, description: {desc_score:.1f} → Score: {field_score:.1f}")

            field_has_failed = False
            if name_score < 90:
                name_fail = True
                feedback_lines.append(
                    f"[NAME GATE] Field '{field_id}' name_score={name_score:.1f} ({self._label_score(name_score)}). Must be ≥ 90.")
                field_has_failed = True
            if type_score < 75:
                quality_fail = True
                feedback_lines.append(
                    f"[TYPE GATE] Field '{field_id}' type_score={type_score:.1f} ({self._label_score(type_score)}). Must be ≥ 75.")
                field_has_failed = True
            if desc_score < 75:
                quality_fail = True
                feedback_lines.append(
                    f"[DESC GATE] Field '{field_id}' desc_score={desc_score:.1f} ({self._label_score(desc_score)}). Must be ≥ 75.")
                field_has_failed = True
            if field_has_failed:
                failed_fields.append(field_id)

        schema_score = sum(field_scores) / len(field_scores) if field_scores else 0.0
        confidence_score = round(schema_score / 100.0, 4)
        retry_required = structure_fail or name_fail or quality_fail
        is_valid = not retry_required

        feedback = "VALIDATION RESULT: Passed (all checks successful)"
        if feedback_lines:
            feedback = "VALIDATION FEEDBACK:\n" + "\n".join(feedback_lines)
            feedback += f"\n\nOverall Schema Score: {schema_score:.2f}/100 ({confidence_score:.4f})"

            if retry_required:
                failed_str = ", ".join(f'"{f}"' for f in failed_fields)
                feedback += f"\n\nFailed Fields: {failed_str}"
                feedback += "\n\nVALIDATION RESULT: Failed (retry required)"
                if structure_fail:
                    feedback += "\n- Structure Gate: Failed (missing components)"
                if name_fail:
                    feedback += "\n- Name Gate: Failed (name scores below threshold)"
                if quality_fail:
                    feedback += "\n- Quality Gate: Failed (type/description scores below threshold)"
                feedback += "\n\nPlease fix the issues highlighted above and regenerate the YAML."

        logger.info(f"✅ Final Result | Valid: {is_valid} | Confidence: {confidence_score:.4f} | Failed: {len(failed_fields)}")
        return is_valid, confidence_score, feedback, failed_fields, field_positions
