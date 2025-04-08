from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from pathlib import Path
import shutil
import uuid
import os
import subprocess

app = FastAPI()

@app.post("/convert/")
async def run_main_basic(pdf: UploadFile = File(...)):
    try:
        # Save uploaded PDF
        temp_dir = Path("temp_files")
        temp_dir.mkdir(exist_ok=True)
        pdf_path = temp_dir / f"{uuid.uuid4()}_{pdf.filename}"
        with open(pdf_path, "wb") as f:
            shutil.copyfileobj(pdf.file, f)

        # Run the main.py script
        result = subprocess.run(
            ["python3", "main.py", str(pdf_path)],
            capture_output=True,
            text=True
        )

        output = {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }

        return JSONResponse(content=output)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/convert-with-metrics/")
async def run_main_with_metrics(
    pdf: UploadFile = File(...),
    ground_truth: UploadFile = File(...)
):
    try:
        # Save uploaded files
        temp_dir = Path("temp_files")
        temp_dir.mkdir(exist_ok=True)

        pdf_path = temp_dir / f"{uuid.uuid4()}_{pdf.filename}"
        with open(pdf_path, "wb") as f:
            shutil.copyfileobj(pdf.file, f)

        gt_path = temp_dir / f"{uuid.uuid4()}_{ground_truth.filename}"
        with open(gt_path, "wb") as f:
            shutil.copyfileobj(ground_truth.file, f)

        # Run the main.py script with ground truth
        result = subprocess.run(
            ["python3", "main.py", str(pdf_path), "--ground-truth", str(gt_path)],
            capture_output=True,
            text=True
        )

        output = {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }

        return JSONResponse(content=output)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
