# PDF to YAML Schema Converter

A command-line and API-based application that processes PDF files containing database schema descriptions and generates structured YAML output. The application uses OpenAI's language models to understand and structure the content, making it easier to integrate with other tools and workflows.

---

## Features

- Extracts text from PDFs (including scanned documents and embedded images)
- Uses OCR for non-selectable text
- Processes schema descriptions using OpenAI
- Generates standardized YAML output
- Validates output structure
- Evaluates accuracy, coverage, performance (optional)
- FastAPI support for API-based conversion
- Comprehensive error handling

---

## Installation

### 1. Prerequisites
- Python 3.13+
- Tesseract OCR

Install Tesseract:
- **macOS:** `brew install tesseract`
- **Ubuntu/Debian:** `sudo apt install tesseract-ocr`
- **Windows:** Download from [Tesseract GitHub](https://github.com/tesseract-ocr/tesseract)

### 2. Python Dependencies
Install all required packages:

```bash
pip install -r requirements.txt
```

### 3. Configuration
Edit `config/constants.py` to set:
- OpenAI API key and model
- Default YAML template path
- Required keywords for parsing schemas

---

## Usage

### 🔁 Command-Line Interface (`main.py`)
To convert a PDF using the command line:

```bash
python main.py input.pdf
```

With optional flags:

```bash
python main.py input.pdf --ground-truth ground_truth/input.yaml --verbose
```

This generates a YAML file in the `output/` folder and, if ground truth is provided, a metrics report in `.txt` format.

---
### FastAPI Web Service (`app.py`) working in progress
### 🚀 FastAPI Web Service (`leniency_app.py`) deprecated
To launch the FastAPI server:

```bash
uvicorn leniency_app:app --reload
```

Then open [http://localhost:8000/docs](http://localhost:8000/docs) for the interactive Swagger UI.

**Available endpoints:**
- `POST /convert/`: Convert a PDF
- `POST /convert-with-metrics/`: Convert and evaluate against a ground truth YAML

---

### 📡 API Access via `curl` or Postman

**Convert only:**
```bash
curl -X POST http://localhost:8000/convert/ \
  -F "pdf=@pdf_files/Iris.pdf"
```

**Convert with ground truth:**
```bash
curl -X POST http://localhost:8000/convert-with-metrics/ \
  -F "pdf=@pdf_files/Iris.pdf" \
  -F "ground_truth=@ground_truth/Iris.yaml"
```

In **Postman**, set method to `POST`, use `form-data`, and upload files using keys:
- `pdf`
- `ground_truth` *(optional)*

### note: the confidence score here is for placeholder features.
---

## Output

The application generates YAML files in the `output/` directory using the format:

```
dataset_descriptions_from_{input_pdf_name}.yaml
```

If metrics are enabled, a matching `.txt` file is created:

```
dataset_descriptions_from_{input_pdf_name}.txt
```

### Example YAML Structure
```yaml
DatasetName:
  - role: system
    content: |
      [Dataset Description]:
      Description of the dataset...

      "Column1": type, detailed description
      "Column2": type, detailed description

      You can access the entire dataset via the "data" variable.
```

---

## Error Handling

Common issues:
- **"Tesseract not found"**: Ensure OCR is installed and in PATH
- **"OpenAI API error"**: Check your API key in `config/constants.py`
- **"Invalid PDF file"**: Ensure file is valid and readable
- **"YAML generation failed"**: Check if the extracted content matches template expectations

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your branch
5. Create a Pull Request

---

## License

This project is licensed under the MIT License — see the `LICENSE` file for details.

