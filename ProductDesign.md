# PDF to YAML Schema Converter

## Overview
A command-line application that processes PDF files containing database schema descriptions and generates structured YAML output. The application uses OpenAI's language models to understand and structure the content, making it easier to integrate with other tools and workflows.

## Architecture

### High-Level Flow
```
Input PDF → PDF Text Extraction → OpenAI Processing → YAML Generation → Output YAML
```

### Components

1. **PDF Text Extractor** (`pdf_extractor/`)
   - Handles PDF file reading and text extraction
   - Uses PyMuPDF for PDF parsing
   - Implements OCR capabilities using Tesseract for scanned documents
   - Provides clean, normalized text output
   - Includes robust error handling for OCR and PDF processing

2. **OpenAI Integration** (`openai_integration/`)
   - Manages communication with OpenAI API
   - Processes extracted text to identify schema descriptions
   - Converts natural language into structured data
   - Handles API errors and rate limiting
   - Uses configurable prompts for consistent output
   - Includes YAML validation and cleanup of API responses

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