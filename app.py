from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from pathlib import Path
import shutil
import uuid
import subprocess
import yaml
from openai import OpenAI
from config.constants import OPENAI_API_KEY_ENV

app = FastAPI()
client = OpenAI()


def get_confidence(feature_text: str, model: str = "gpt-4", temperature: float = 0.2) -> float:
    prompt = f"""
You are evaluating the clarity and confidence of dataset feature definitions.
For the following line, rate your confidence (from 0 to 100) that the column name, type, and description are all correct and complete. Only respond with a number like 97.25 or 83.00. No explanation.

Line:
{feature_text}
"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt.strip()}],
            temperature=temperature,
            max_tokens=6
        )
        score_text = response.choices[0].message.content.strip()
        score = float(score_text)
        return round(max(0.0, min(score, 100.0)), 2)
    except Exception as e:
        print(f"[LLM Confidence Scoring Error] {e}")
        return 0.0


def extract_structured_output(yaml_path: Path):
    if not yaml_path.exists():
        return [], 0.0

    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)

    tables = []
    total_score = 0.0
    field_count = 0

    for dataset, messages in data.items():
        for msg in messages:
            if msg["role"] == "system":
                fields = []
                for line in msg["content"].splitlines():
                    if line.strip().startswith('"') and ":" in line:
                        try:
                            name_part, rest = line.strip().split(":", 1)
                            name = name_part.strip().strip('"')
                            type_part, *desc_part = rest.split(",", 1)
                            type_ = type_part.strip()
                            description = desc_part[0].strip() if desc_part else ""
                            confidence_score = get_confidence(line.strip())
                            total_score += confidence_score
                            field_count += 1
                            fields.append({
                                "name": name,
                                "type": type_,
                                "description": description,
                                "confidence_score": confidence_score
                            })
                        except Exception:
                            continue
                tables.append({
                    "name": dataset,
                    "fields": fields
                })

    overall_confidence = round(total_score / field_count, 2) if field_count else 0.0
    return tables, overall_confidence


@app.post("/convert/")
async def run_main_basic(pdf: UploadFile = File(...)):
    try:
        temp_dir = Path("temp_files")
        temp_dir.mkdir(exist_ok=True)
        pdf_path = temp_dir / f"{uuid.uuid4()}_{pdf.filename}"
        with open(pdf_path, "wb") as f:
            shutil.copyfileobj(pdf.file, f)

        result = subprocess.run(
            ["python3", "main.py", str(pdf_path)],
            capture_output=True,
            text=True
        )

        output_dir = Path("output")
        yaml_output = output_dir / f"dataset_descriptions_from_{pdf_path.stem}.yaml"
        tables, overall_confidence = extract_structured_output(yaml_output)

        return JSONResponse(content={
            "tables": tables,
            "overall_confidence": overall_confidence,
            "yaml_download_path": str(yaml_output),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/convert-with-metrics/")
async def run_main_with_metrics(
    pdf: UploadFile = File(...),
    ground_truth: UploadFile = File(...)
):
    try:
        temp_dir = Path("temp_files")
        temp_dir.mkdir(exist_ok=True)

        pdf_path = temp_dir / f"{uuid.uuid4()}_{pdf.filename}"
        with open(pdf_path, "wb") as f:
            shutil.copyfileobj(pdf.file, f)

        gt_path = temp_dir / f"{uuid.uuid4()}_{ground_truth.filename}"
        with open(gt_path, "wb") as f:
            shutil.copyfileobj(ground_truth.file, f)

        result = subprocess.run(
            ["python3", "main.py", str(pdf_path), "--ground-truth", str(gt_path)],
            capture_output=True,
            text=True
        )

        output_dir = Path("output")
        yaml_output = output_dir / f"dataset_descriptions_from_{pdf_path.stem}.yaml"
        tables, overall_confidence = extract_structured_output(yaml_output)

        return JSONResponse(content={
            "tables": tables,
            "overall_confidence": overall_confidence,
            "yaml_download_path": str(yaml_output),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
