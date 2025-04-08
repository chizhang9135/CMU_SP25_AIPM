from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from pathlib import Path
import shutil
import uuid

from pdf_converter.converter import PDFConverter
from config.constants import DEFAULT_YAML_TEMPLATE

app = FastAPI()

@app.post("/convert/")
async def convert_pdf(pdf: UploadFile = File(..., media_type="application/pdf")):
    try:
        temp_dir = Path("temp_files")
        temp_dir.mkdir(exist_ok=True)
        pdf_path = temp_dir / f"{uuid.uuid4()}_{pdf.filename}"
        with open(pdf_path, "wb") as f:
            shutil.copyfileobj(pdf.file, f)

        converter = PDFConverter(template_path=DEFAULT_YAML_TEMPLATE, verbose=True)
        yaml_path, json_response = converter.convert_pdf(str(pdf_path))

        return JSONResponse(content={
            "yaml_download_path": str(yaml_path),
            **json_response
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})