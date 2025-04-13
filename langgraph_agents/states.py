from typing import Dict, List, Optional, TypedDict, Any
from pathlib import Path

class PDFState(TypedDict):
    """State for PDF processing workflow"""
    pdf_path: str                      # Path to input PDF
    extracted_text: str                # Raw text from PDF
    current_yaml: Optional[Dict]       # Current YAML content
    iteration_count: int               # Current iteration number
    confidence_score: float            # Overall confidence score
    validation_feedback: Optional[str]  # Feedback from validator
    is_final: bool                     # Whether this is final output
    error: Optional[str]               # Error message if any
    stacktrace: Optional[str]          # Stack trace if error occurs
    output_path: Optional[str]         # Path to output YAML file
    json_obj: Optional[Dict]           # JSON object

class WorkflowConfig:
    """Configuration for the workflow"""
    def __init__(
        self,
        max_iterations: int = 3,
        confidence_threshold: float = 0.8
    ):
        self.max_iterations = max_iterations
        self.confidence_threshold = confidence_threshold
