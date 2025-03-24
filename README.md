# PDF to YAML Schema Converter

A command-line application that processes PDF files containing database schema descriptions and generates structured YAML output. The application uses OpenAI's language models to understand and structure the content, making it easier to integrate with other tools and workflows.

## Features

- Extracts text from PDFs (including scanned documents and embedded images)
- Uses OCR for non-selectable text
- Processes schema descriptions using OpenAI
- Generates standardized YAML output
- Validates output structure
- Comprehensive error handling

## Installation

### 1. Prerequisites

- Python 3.13+
- Tesseract OCR

#### Installing Tesseract OCR:
- **macOS:** `brew install tesseract`
- **Ubuntu/Debian:** `sudo apt install tesseract-ocr`
- **Windows:** Download from [Tesseract GitHub](https://github.com/tesseract-ocr/tesseract)

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

Basic usage:
```bash
python main.py input.pdf
```

With verbose output:
```bash
python main.py input.pdf --verbose
```

Using a custom template:
```bash
python main.py input.pdf --template path/to/template.yaml
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
└── test_files/            # Test PDF files
```

## Output

The application generates YAML files in the `output` directory with the naming format:
```
dataset_descriptions_from_{input_pdf_name}.yaml
```

Example output structure:
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
- "Tesseract not found": Ensure Tesseract OCR is installed and in your PATH
- "OpenAI API error": Check the API key in `config/constants.py`
- "Invalid PDF file": Verify the input file is a valid PDF
- "YAML generation failed": Check the input PDF format and content

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

