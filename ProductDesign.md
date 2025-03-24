# PDF to YAML Schema Converter

## Overview
A command-line application that processes PDF files containing database schema descriptions and generates structured YAML output. The application leverages LangGraph for orchestration and OpenAI's language models to understand and structure the content, making it easier to integrate with other tools and workflows.

## Architecture

### Framework Selection: LangChain vs LangGraph Trade-offs

We evaluated both LangChain and LangGraph for this application:

#### LangChain Characteristics
- Traditional sequential chain-based workflows
- Simple implementation for linear processes
- Built-in document loading and processing tools
- Basic memory management through Memory classes
- Mature but less flexible for complex state handling

#### LangGraph Benefits
- Graph-based state machine architecture
- Superior error recovery and retry mechanisms
- Explicit state management for complex workflows
- Better handling of edge cases and validation loops
- Visual workflow debugging capabilities
- Native support for parallel processing
- More granular control over the conversion pipeline

#### Decision
For this application, we chose LangGraph because:
1. Schema conversion often requires multiple validation and refinement cycles
2. Error handling needs sophisticated recovery paths (e.g., OCR failures, schema ambiguities)
3. The graph-based architecture allows for:
   - Parallel processing of multiple schema sections
   - Dynamic branching based on content complexity
   - Explicit state tracking for partial successes
4. Visual debugging helps optimize the conversion pipeline
5. Future extensibility for more complex workflows

### High-Level Flow
```
                        ┌─── Validation Loop ───┐
                        │                       │
Input PDF → Text Extraction → Schema Analysis → YAML Generation → Output
                        │                       │
                        └─── Error Recovery ────┘
```

### Components

1. **PDF Text Extractor** (`pdf_extractor/`)
   - Handles PDF file reading and text extraction
   - Uses PyMuPDF for PDF parsing
   - Implements OCR capabilities using Tesseract for scanned documents
   - Provides clean, normalized text output
   - Includes robust error handling for OCR and PDF processing

2. **LangGraph Integration** (`langgraph_integration/`)
   - Implements state machine for document processing
   - Defines nodes for schema identification and transformation
   - Manages parallel processing of document sections
   - Handles state transitions and error recovery
   - Implements validation and refinement cycles
   - Provides visual workflow monitoring
   - Includes comprehensive retry strategies

3. **YAML Generator** (`yaml_generator/`)
   - Generates standardized YAML output
   - Implements templating for consistent formatting
   - Validates output structure
   - Saves files to `/output` directory with standardized naming
   - Includes comprehensive error handling for file operations

4. **Configuration** (`config/`)
   - Centralizes all configuration settings
   - Manages environment variables and constants
   - Stores template files and system prompts
   - Provides easy customization of application behavior

### Implementation Details

#### Configuration
- Templates stored in `config/templates/`
- Environment variables for API keys and settings
- Configurable OpenAI parameters (model, temperature, etc.)
- Constants defined in `config/constants.py`

#### Error Handling
- Custom exception classes for each component
- Detailed logging with debug mode
- Graceful failure handling with informative messages
- Proper cleanup of temporary files and resources

#### Output Format
- Standardized YAML structure
- Files saved as `dataset_descriptions_from_{pdf_name}.yaml`
- All outputs stored in `/output` directory
- Consistent formatting and structure

## Command-Line Interface

```bash
python main.py <input_pdf> [--template TEMPLATE] [--verbose]
```

### Arguments
- `input_pdf`: Path to the PDF file to process
- `--template`: Optional path to custom YAML template (default: config/templates/default.yaml)
- `--verbose`: Enable detailed logging output

## Dependencies
- PyMuPDF (>=1.25.0): PDF parsing
- Pillow (>=11.0.0): Image processing
- pytesseract (>=0.3.13): OCR capabilities
- OpenAI (>=1.68.0): API integration
- PyYAML (>=6.0.0): YAML processing
- python-dotenv (>=1.0.0): Environment management

## Installation
1. Install Python 3.13+
2. Install Tesseract OCR
3. Install Python dependencies: `pip install -r requirements.txt`
4. Set up environment variables in `.env` file:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage Example
```bash
python main.py example.pdf --verbose
```

This will:
1. Extract text from example.pdf
2. Process the content using OpenAI
3. Generate a YAML file in the /output directory
4. Name the output file as dataset_descriptions_from_example.yaml

## Error Messages
Common error messages and their solutions:
- "Tesseract not found": Install Tesseract OCR and ensure it's in your PATH
- "OpenAI API key not found": Check your .env file configuration
- "Invalid PDF file": Ensure the input file is a valid PDF
- "YAML generation failed": Check the input PDF format and content 