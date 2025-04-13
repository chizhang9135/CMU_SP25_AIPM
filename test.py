import asyncio
from pathlib import Path
from langgraph_agents.workflow import PDFToYAMLWorkflow

async def test_pdf_workflow():
    """Test the PDF to YAML workflow"""
    # Sample test PDF path (replace with an actual small, valid PDF for local testing)
    sample_pdf = "pdf_files/Adult.pdf"
    template_path = "config/templates/default.yaml"

    # Validate input files exist
    assert Path(sample_pdf).exists(), "Sample PDF not found."
    assert Path(template_path).exists(), "Template file not found."

    # Initialize workflow
    workflow = PDFToYAMLWorkflow(template_path=template_path)

    try:
        # Run workflow
        state = await workflow.run(sample_pdf)

        # Validate results
        yaml_path = state["output_path"]
        json_response = state["json_obj"]

        print("YAML file generated at:", yaml_path)
        print("\nJSON response:")
        print(json_response)

        assert Path(yaml_path).exists(), "YAML output file not created."
        assert isinstance(json_response, dict), "JSON response is not a dictionary."

    except Exception as e:
        print("Test failed with exception:", str(e))
        raise

def main():
    """Run the tests"""
    try:
        asyncio.run(test_pdf_workflow())
    except Exception as e:
        print(f"Test suite failed: {e}")
        raise

if __name__ == "__main__":
    main()