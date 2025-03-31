#!/bin/zsh

# Define paths
PDF_DIR="./pdf_files"
YAML_DIR="./ground_truth"
PYTHON_SCRIPT="./main.py"

# Loop through each PDF file
for pdf_path in "$PDF_DIR"/*.pdf; do
  # Get the base name without extension
  base_name=$(basename "$pdf_path" .pdf)

  # Construct the corresponding YAML file path
  yaml_path="$YAML_DIR/$base_name.yaml"

  # Check if YAML file exists
  if [[ -f "$yaml_path" ]]; then
    echo "Running: $pdf_path with $yaml_path"
    python3 "$PYTHON_SCRIPT" "$pdf_path" --ground-truth "$yaml_path"
  else
    echo "Skipping: $pdf_path (no matching YAML found)"
  fi
done

