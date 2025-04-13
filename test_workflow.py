import asyncio
from pathlib import Path
from langgraph_agents.workflow import PDFToYAMLWorkflow

async def test_workflow():
    # Initialize workflow
    workflow = PDFToYAMLWorkflow()
    
    # Test with a sample PDF (using the one from your existing tests)
    pdf_path = "pdf_files/Adult.pdf"  # Using the same path from your test.py
    
    print(f"Testing workflow with PDF: {pdf_path}")
    
    try:
        # Run the workflow
        final_state = await workflow.run(pdf_path)
        
        # Check the results
        print("\nWorkflow Results:")
        print(f"Extraction successful: {bool(final_state.get('extracted_text'))}")
        print(f"YAML generated: {bool(final_state.get('current_yaml'))}")
        print(f"Iterations: {final_state.get('iteration_count')}")
        print(f"Confidence score: {final_state.get('confidence_score')}")
        print(f"Is final: {final_state.get('is_final')}")
        print(f"Output path: {final_state.get('output_path')}")
        print(f"JSON object: {final_state.get('json_obj')}")
        
        # Enhanced error reporting
        if final_state.get('error'):
            print("\nError occurred:")
            print(f"Error message: {final_state['error']}")
            if final_state.get('stacktrace'):
                print("\nStack trace:")
                print(final_state['stacktrace'])
        else:
            print("Error: None")
        
        if final_state.get('current_yaml'):
            print("\nGenerated YAML structure:")
            print(final_state['current_yaml'])
            
    except Exception as e:
        print(f"Workflow failed with error: {str(e)}")
        import traceback
        print("\nStack trace:")
        print(traceback.format_exc())

if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_workflow()) 