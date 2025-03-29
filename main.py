#!/usr/bin/env python3
import argparse
import sys
import logging
from pathlib import Path

from pdf_extractor.extractor import PDFTextExtractor
from openai_integration.client import OpenAIClient, OpenAIClientError
from yaml_generator.templater import YAMLGenerator, YAMLGeneratorError
from config.constants import DEFAULT_YAML_TEMPLATE

def setup_logging(verbose: bool = False) -> logging.Logger:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(message)s'
    )
    return logging.getLogger(__name__)

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
        default=DEFAULT_YAML_TEMPLATE,
        help=f'Path to the YAML template file (default: {DEFAULT_YAML_TEMPLATE})'
    )
    parser.add_argument(
        '--ground-truth',
        type=str,
        help='Path to the ground truth YAML file for evaluation'
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

    # Convert paths to Path objects
    pdf_path = Path(args.input_pdf).resolve()
    template_path = Path(args.template).resolve()

    # Validate input files
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

        if not raw_text.strip():
            logger.error("No text could be extracted from the PDF")
            sys.exit(1)
        logger.debug(f"Extracted {len(raw_text)} characters from PDF")

        # Process with OpenAI
        logger.info("Processing with OpenAI")
        ai_client = OpenAIClient()
        try:
            processed_content = ai_client.process_pdf_text(raw_text)
            logger.debug(f"Received response from OpenAI with {len(processed_content)} datasets")
        except OpenAIClientError as e:
            logger.error(f"OpenAI processing failed: {e}")
            sys.exit(1)

        # Generate and save YAML output
        logger.info("Generating YAML output")
        try:
            generator = YAMLGenerator(template_path)
            output_path = generator.save(processed_content, pdf_path)
            logger.info(f"Output written to: {output_path}")

            # Run metrics if ground truth is provided
            if args.ground_truth:
                from metrics import MetricsEvaluator
                try:
                    logger.info("Running metrics evaluation")
                    evaluator = MetricsEvaluator(args.ground_truth, output_path)
                    dataset_key = next(iter(evaluator.ground_truth))

                    acc_msg, acc = evaluator.accuracy(dataset_key)
                    cov_msg, cov = evaluator.coverage(dataset_key)

                    report_path = output_path.with_suffix('.txt')
                    with open(report_path, 'w') as report_file:
                        report_file.write("--- Accuracy Report ---\n")
                        report_file.write(acc_msg + "\n")
                        report_file.write(f"Accuracy: {acc:.2%}\n\n")
                        report_file.write("--- Coverage Report ---\n")
                        report_file.write(cov_msg + "\n")
                        report_file.write(f"Coverage: {cov:.2%}\n")

                    logger.info(f"Metrics report written to: {report_path}")

                except Exception as e:
                    logger.error(f"Evaluation failed: {str(e)}")
                    if args.verbose:
                        logger.exception("Detailed error during evaluation:")

        except YAMLGeneratorError as e:
            logger.error(f"YAML generation failed: {e}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Unexpected error while processing PDF: {str(e)}")
        if args.verbose:
            logger.exception("Detailed error information:")
        sys.exit(1)

if __name__ == '__main__':
    main()
