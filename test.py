from pdf_converter.converter import PDFConverter
from pathlib import Path

def test_pdf_converter():
    # Sample test PDF path (replace with an actual small, valid PDF for local testing)
    sample_pdf = "pdf_files/Adult.pdf"
    template_path = "config/templates/default.yaml"


    assert Path(sample_pdf).exists(), "Sample PDF not found."
    assert Path(template_path).exists(), "Template file not found."

    # Initialize converter
    converter = PDFConverter(template_path=template_path, verbose=True)

    # Convert PDF to YAML
    try:
        yaml_path, json_response = converter.convert_pdf(sample_pdf)

        print("YAML file generated at:", yaml_path)
        print("JSON response:")
        print(json_response)

        assert Path(yaml_path).exists(), "YAML output file not created."
        assert isinstance(json_response, dict), "JSON response is not a dictionary."

    except Exception as e:
        print("Test failed with exception:", str(e))
        assert False, "Exception occurred during conversion."

if __name__ == "__main__":
    test_pdf_converter()