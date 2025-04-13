from typing import Dict, Tuple, Optional
from openai_integration.client import OpenAIClient
from langgraph_agents.states import PDFState, WorkflowConfig

class SchemaValidator:
    """Validator agent for checking YAML schema and suggesting corrections"""
    
    def __init__(self, config: WorkflowConfig):
        self.config = config
        self.openai_client = OpenAIClient()
    
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
        # TODO Always return valid with high confidence
        return True, 1.0, None
