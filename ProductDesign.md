# PDF to YAML Schema Converter

## Overview
A command-line application that processes PDF files containing database schema descriptions and generates structured YAML output. The application leverages LangGraph for orchestration and OpenAI's language models to understand and structure the content, making it easier to integrate with other tools and workflows.

## Architecture

### Framework Selection: LangGraph Implementation

We've implemented a graph-based workflow using LangGraph that provides:

- **State Management**: Explicit state tracking throughout the conversion process
- **Validation Loops**: Multiple passes for refinement and error correction
- **Error Recovery**: Graceful handling of extraction and parsing failures
- **Confidence Scoring**: Built-in evaluation of output quality

#### LangGraph Benefits
- Graph-based state machine architecture
- Explicit state management for complex workflows
- Confidence-based output evaluation
- Automatic retries with feedback incorporation
- Asynchronous execution for better performance
- JSON output for easy integration with other systems

### High-Level Flow
```
                        ┌─── Validation & Refinement Loop ───┐
                        │                                    │
Input PDF → Text Extraction → YAML Generation → Validation →  Output Generation
                        │                                    │
                        └─── Feedback Incorporation ───────-─┘
```

### Components

1. **PDF Text Extractor** (`pdf_extractor/`)
   - Handles PDF file reading and text extraction
   - Uses PyMuPDF for PDF parsing
   - Provides clean, normalized text output
   - Includes robust error handling

2. **LangGraph Workflow** (`langgraph_agents/`)
   - Implements state machine for document processing using `StateGraph`
   - Defines nodes for extraction, generation, validation, and output
   - Manages state transitions with conditional routing
   - Implements confidence-based termination criteria
   - Provides comprehensive error handling with stack traces
   - Supports asynchronous execution of all operations

3. **OpenAI Integration** (`openai_integration/`)
   - Implements asynchronous API calls to OpenAI models
   - Manages prompt templates for generation and validation
   - Handles YAML parsing of model responses
   - Implements error handling for API calls

4. **YAML Generator** (`output_generator/`)
   - Generates standardized YAML output
   - Implements templating for consistent formatting
   - Transforms YAML to JSON for API compatibility
   - Saves files with standardized naming
   - Includes confidence scores in output

5. **Configuration** (`config/`)
   - Centralizes all configuration settings
   - Manages environment variables and constants
   - Stores template files and system prompts

### Implementation Details

#### Workflow State
The workflow maintains a comprehensive state object (`PDFState`) containing:
- PDF path and extracted text
- Current YAML representation
- Iteration count for refinement loops
- Confidence score for output quality
- Validation feedback for improvements
- Error information with full stack traces
- Output file paths and JSON representation

#### Confidence-Based Validation
- Each generated YAML is evaluated for quality
- Confidence scores determine whether to continue refinement
- Configurable threshold for acceptable output quality
- Maximum iteration limit to prevent infinite loops

#### Async Execution
- All components implement asynchronous interfaces
- OpenAI API calls are non-blocking
- Full async support from extraction to output generation

#### Error Handling
- Custom exception classes for each component
- Detailed stack traces for debugging
- Graceful failure handling with informative messages

#### Output Format
- Standardized YAML structure
- JSON representation for API compatibility
- Includes confidence scores and metadata
- Consistent table and field structure

## Command-Line Interface

```bash
python main.py <input_pdf> [--template TEMPLATE] [--verbose]
```

### Arguments
- `input_pdf`: Path to the PDF file to process
- `--template`: Optional path to custom YAML template (default: config/templates/default.yaml)
- `--verbose`: Enable detailed logging output

## API Usage
The workflow can be used programmatically:

```python
import asyncio
from langgraph_agents.workflow import PDFToYAMLWorkflow

async def process_pdf(pdf_path):
    workflow = PDFToYAMLWorkflow(template_path="config/templates/default.yaml")
    state = await workflow.run(pdf_path)
    
    # Access results
    yaml_path = state["output_path"]
    json_response = state["json_obj"]
    confidence = state["confidence_score"]
    
    return yaml_path, json_response

# Run the workflow
yaml_path, json_response = asyncio.run(process_pdf("example.pdf"))
```

## Dependencies
- PyMuPDF (>=1.25.0): PDF parsing
- LangGraph (>=0.0.30): Workflow orchestration
- OpenAI (>=1.68.0): API integration
- PyYAML (>=6.0.0): YAML processing
- python-dotenv (>=1.0.0): Environment management

## Installation
1. Install Python 3.13+
2. Install Python dependencies: `pip install -r requirements.txt`
3. Set up environment variables in `.env` file:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage Example
```bash
python main.py example.pdf --verbose
```

This will:
1. Extract text from example.pdf
2. Process the content using the LangGraph workflow
3. Generate a YAML file with dataset descriptions
4. Include a JSON representation with confidence scores

## Testing
Run the test suite to validate the workflow:

```bash
python test.py
```

The tests verify:
- PDF text extraction
- YAML generation
- JSON conversion
- End-to-end workflow 