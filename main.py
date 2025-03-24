#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

from pdf_extractor.extractor import PDFTextExtractor
from content_processor.parser import ContentParser
from openai_integration.client import OpenAIClient
from yaml_generator.templater import YAMLGenerator
from utils.helpers import setup_logging

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Process PDF files and generate structured YAML output'
    )
    parser.add_argument(
        'input_pdf',
        type=str,
        help='Path to the input PDF file'
    )
    parser.add_argument(
        '--template',
        type=str,
        default='config/templates/default.yaml',
        help='Path to the YAML template file (default: config/templates/default.yaml)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    return parser.parse_args()

def main():
    args = parse_arguments()
    logger = setup_logging(verbose=args.verbose)

    # Validate input files
    pdf_path = Path(args.input_pdf)
    template_path = Path(args.template)
    
    if not pdf_path.exists():
        logger.error(f"Input PDF file not found: {pdf_path}")
        sys.exit(1)
    if not template_path.exists():
        logger.error(f"Template file not found: {template_path}")
        sys.exit(1)

    try:
        # Extract text from PDF
        logger.info(f"Processing PDF: {pdf_path}")
        extractor = PDFTextExtractor(str(pdf_path))
        raw_text = extractor.extract_text()

        # Process and structure the content
        logger.info("Analyzing content structure")
        parser = ContentParser()
        structured_content = parser.parse(raw_text)

        # Process with OpenAI
        logger.info("Processing with OpenAI")
        ai_client = OpenAIClient()
        processed_content = ai_client.process_content(structured_content)

        # Generate YAML output
        logger.info("Generating YAML output")
        generator = YAMLGenerator(template_path)
        yaml_output = generator.generate(processed_content)

        # Write output
        output_path = pdf_path.with_suffix('.yaml')
        with open(output_path, 'w') as f:
            f.write(yaml_output)
        logger.info(f"Output written to: {output_path}")

    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()