# PDF to YAML Schema Converter

A command-line application that processes PDF files containing database schema descriptions and generates structured YAML output. The application uses OpenAI's language models to understand and structure the content, making it easier to integrate with other tools and workflows.

## Features
- Extracts text from PDFs (including scanned documents and embedded images)
- Uses OCR for non-selectable text
- Processes schema descriptions using OpenAI
- Generates standardized YAML output
- Validates output structure
- Evaluates YAML quality and performance with built-in metrics
- Comprehensive error handling

## Installation

### 1. Prerequisites
- Python 3.13+
- Tesseract OCR

Installing Tesseract OCR:
- **macOS**: `brew install tesseract`
- **Ubuntu/Debian**: `sudo apt install tesseract-ocr`
- **Windows**: Download from Tesseract GitHub

### 2. Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configuration
The application configuration is managed through `config/constants.py`, including:
- OpenAI API settings (API key, model, temperature)
- File paths and templates
- Schema keywords and required fields

## Usage

### Basic Conversion
```bash
python3 main.py input.pdf
```

### Using a Custom Template
```bash
python3 main.py input.pdf --template path/to/template.yaml
```

### Evaluating Output with Metrics
```bash
python3 main.py input.pdf --ground-truth ground_truth/ground_truth_demo.yaml
```

This will:
1. Extract content from the PDF
2. Send the content to OpenAI
3. Generate a YAML file
4. Evaluate it against the provided ground truth
5. Write a report to the same directory (e.g., `output/input.txt`)

## Metrics Report Format

```text
--- Accuracy Report ---
<Details on feature matches or mismatches>
Accuracy: XX.XX%

--- Coverage Report ---
<Details on missing features>
Coverage: XX.XX%

--- Performance Report ---
Latency: X.XX seconds
Memory Usage: XX.XX MB

--- Token Usage ---
Input Tokens (estimated): XXXX
Output Tokens (estimated): XXXX
```

## Project Structure
```
.
├── config/
│   ├── constants.py         # Configuration constants and API keys
│   ├── prompts/            # OpenAI prompt templates
│   └── templates/          # YAML validation templates
├── pdf_extractor/          # PDF text extraction module
├── openai_integration/     # OpenAI API integration
├── yaml_generator/         # YAML generation and validation
├── output/                 # Generated YAML files
├── test_files/             # Test PDF files
├── metrics/                # Accuracy, coverage, and performance evaluation
```

## Output
The application generates YAML files in the `output/` directory with the naming format:
```
dataset_descriptions_from_{input_pdf_name}.yaml
```

### Example YAML Output
```yaml
DatasetName:
  - role: system
    content: |
      [Dataset Description]:
      Description of the dataset...

      "Column1": type, detailed description
      "Column2": type, detailed description

      You can access the entire dataset via the "data" variable.

      Additional notes and handling instructions...
```

## Error Handling
Common errors and solutions:

- **"Tesseract not found"**: Ensure Tesseract OCR is installed and in your PATH
- **"OpenAI API error"**: Check the API key in `config/constants.py`
- **"Invalid PDF file"**: Verify the input file is a valid PDF
- **"YAML generation failed"**: Check the input PDF format and content

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License
This project is licensed under the MIT License - see the LICENSE file for details.

