# PDF to YAML Schema Converter API Specification

## Base URL
```
https://api.schemaconverter.com/v1
```

## Endpoint

### Upload and Process PDF

#### POST /convert
Uploads a PDF file and returns the conversion results.

##### Request
```http
POST /convert
Content-Type: multipart/form-data

{
  "file": <binary_pdf_file>
}
```

##### Response
```json
{
  "tables": [
    {
      "name": "users",
      "fields": [
        {
          "name": "id",
          "type": "integer",
          "description": "Unique identifier for the user",
          "confidence_score": 0.95
        },
        {
          "name": "name",
          "type": "string",
          "description": "Full name of the user",
          "confidence_score": 0.92
        }
      ]
    }
  ],
  "yaml_download_url": "https://api.schemaconverter.com/v1/download/conversion_123.yaml"
}
```

## Error Responses

### 400 Bad Request
```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Invalid PDF file format",
    "details": "The uploaded file is not a valid PDF"
  }
}
```

### 500 Internal Server Error
```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An error occurred during processing",
    "details": "OCR processing failed"
  }
}
```

## Example Usage

### Upload and Process PDF
```bash
curl -X POST https://api.schemaconverter.com/v1/convert \
  -F "file=@schema.pdf"
```
