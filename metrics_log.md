# Metrics Usage Guide

This guide explains how to use the built-in evaluation metrics available in the PDF-to-YAML pipeline.

## Overview
After converting a PDF into a structured YAML file, you can optionally evaluate the quality and performance of the generated output by comparing it with a ground truth file.

The metrics system supports the following evaluations:

- **Accuracy**: Percentage of correctly matched features (by name and type).
- **Coverage**: Percentage of features present (based on names).
- **Latency**: Time taken to process the input via OpenAI.
- **Memory Usage**: Peak memory usage during processing.
- **Token Usage**: Estimated token count for input and output.

## How to Use

```bash
python3 main.py pdf_path --ground-truth ground_truth_yaml_path
```

### Prerequisites
You need:
- A PDF file to process (e.g., `demo.pdf`)
- A ground truth YAML file (e.g., `ground_truth/ground_truth_demo.yaml`)
- A valid YAML template (default is already configured)

### Example Command
```bash
python3 main.py demo.pdf --ground-truth ground_truth/ground_truth_demo.yaml
```

This will:
1. Extract content from `demo.pdf`
2. Send the content to OpenAI
3. Generate a YAML file (e.g., `output/demo.yaml`)
4. Evaluate it against the provided ground truth
5. Write a report (e.g., `output/demo.txt`)

## Output Report Format
The generated `.txt` report will include:

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

## Notes
- No need to use `--verbose` for normal runs.
- The report is automatically created in the same directory as the YAML output.
- Token estimation assumes 4 tokens per word.

For more advanced use (like logging intermediate steps), consider adding the `--verbose` flag.

---

Feel free to update the metric logic or integrate it with automated tests or CI pipelines!

