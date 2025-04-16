# PDF to YAML Schema Converter

A command-line and API-based application that processes PDF files containing database schema descriptions and generates structured YAML output. The application uses OpenAI's language models to structure and clarify schema content, making it easier to integrate with other data workflows and validation pipelines.

---

## Features

- Extracts text from PDFs (including scanned documents and embedded images)
- Uses OCR for non-selectable or image-based text
- Interprets schema descriptions using OpenAI
- Generates clean, consistent YAML output
- Validates output structure using a configurable template
- Optionally evaluates accuracy, coverage, latency, memory, and token usage
- Confidence scoring (LLM-based) for each column feature
- FastAPI web service for integration
- Comprehensive error handling and logging

---

## 🚀 Deploy & Run with Docker

This project supports a one-command deployment using Docker. No need to install Python, Tesseract, or dependencies manually.

### 1. Prerequisites

- [Docker](https://www.docker.com/) installed
- [Docker Compose V2](https://docs.docker.com/compose/install/) or use `docker compose` (Docker v20.10+) 

> 🛑 **Note:** If your Docker requires elevated privileges, you may need to run the following commands with `sudo`.

### 2. Clone the Repository

```bash
git clone https://github.com/your-org/CMU_SP25_AIPM.git
cd CMU_SP25_AIPM
```

### 3. Run the App

```bash
./run.sh
```

You’ll be prompted to enter your **OpenAI API key**. Input is hidden for security:

```
🔐 Enter your OpenAI API key below.
(Paste or type your key — input will be hidden for security):
```

If you see a "permission denied" Docker error, run the script using `sudo`:

```bash
sudo ./run.sh
```

### 4. Access the Web API

Once running, open your browser:

- **Local:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Remote/public:** `http://<your-ip>:8000/docs`

Use the `/convert/` endpoint to upload PDF files and receive structured YAML output.

---

## Manual Installation

### 1. Prerequisites

- Python 3.13+
- Tesseract OCR

Install Tesseract:

- **macOS:**

  ```bash
  brew install tesseract
  ```

- **Ubuntu/Debian:**

  ```bash
  sudo apt install tesseract-ocr
  ```

- **Windows:**

  Download and install from [Tesseract GitHub](https://github.com/tesseract-ocr/tesseract)

---

### 2. Python Dependencies

Install required Python packages:

```bash
pip install -r requirements.txt
```

---

### 3. Configuration

Edit `config/constants.py` to set:

- OpenAI API key (or use the `OPENAI_API_KEY` environment variable)
- Model (e.g., `"gpt-4"`)
- Default YAML template path
- Schema parsing keywords

---

## Usage

### 🔧 Command-Line Interface (`main.py`)

Basic conversion:

```bash
python main.py input.pdf
```

With ground truth evaluation and logging:

```bash
python main.py input.pdf --ground-truth ground_truth/input.yaml --verbose
```

Output is saved to the `output/` directory.

---

### 🚀 FastAPI Web Service

#### ✅ Stable API (`app.py`)

Start the server:

```bash
uvicorn app:app --reload
```

Visit [http://localhost:8000/docs](http://localhost:8000/docs) for the Swagger UI.

**Endpoints:**

- `POST /convert/` – Convert PDF to YAML and return structured JSON
- `POST /convert-with-metrics/` – Convert and evaluate with ground truth (returns metrics report in `.txt`, not JSON)

#### 🧪 Experimental API (`experiment_app.py`)

An attempt to refactor the codebase for better modularity and maintainability. Uses internal `PDFConverter` logic and returns structured JSON responses.

> **Note:** This API does not support ground truth or metrics evaluation. It is lightweight and focused on generation only.

Start the server:

```bash
uvicorn experiment_app:app --reload
```

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

In Postman, use `POST` with `form-data` and upload files under keys:
- `pdf`
- `ground_truth` *(optional)*

---

## Output

### 📄 YAML File

Saved in `output/` with the format:

```
dataset_descriptions_from_{input_pdf_name}.yaml
```

If evaluated:

```
dataset_descriptions_from_{input_pdf_name}.txt
```

### 📊 JSON Response (both APIs)

Both `/convert/` endpoints return:

```json
{
  "tables": [
    {
      "name": "DatasetName",
      "fields": [
        {
          "name": "Column1",
          "type": "string",
          "description": "Some description here",
          "confidence_score": 94.23
        },
        ...
      ]
    }
  ],
  "overall_confidence": 92.11,
  "yaml_download_path": "output/dataset_descriptions_from_input.pdf.yaml",
  "stdout": "...",
  "stderr": "...",
  "return_code": 0
}
```

- `confidence_score`: Estimated by GPT for each column definition
- `overall_confidence`: Average of all feature confidence scores

---

## Error Handling

| Issue                     | Fix                                                   |
|--------------------------|--------------------------------------------------------|
| `Tesseract not found`     | Ensure OCR is installed and in system PATH             |
| `OpenAI API error`        | Confirm your key in `constants.py` or environment      |
| `Invalid PDF file`        | Verify file format and encoding                        |
| `YAML generation failed`  | Check if text matches template expectations            |

---

## Contributing

1. Fork the repository  
2. Create a feature branch  
3. Commit your changes  
4. Push your branch  
5. Submit a Pull Request

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
