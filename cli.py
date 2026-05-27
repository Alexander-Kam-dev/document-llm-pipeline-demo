"""CLI tool for processing PDFs.

Extended with a report-only evaluation command:
  python cli.py eval --mode llm

"""

import sys
import argparse
from pathlib import Path

from app.pipeline import process_document
from app.storage import storage
from app.eval import evaluate_samples, print_report


def _cmd_process(args: argparse.Namespace) -> int:
    pdf_path = Path(args.pdf_file)
    if not pdf_path.exists():
        print(f"Error: File not found: {pdf_path}")
        return 1

    if pdf_path.suffix.lower() != ".pdf":
        print("Error: File must be a PDF")
        return 1

    print(f"Processing: {pdf_path}")
    print(f"Mode: {args.mode}")
    print("-" * 50)

    try:
        pdf_bytes = pdf_path.read_bytes()
        extracted_data = process_document(pdf_bytes, mode=args.mode)

        result = storage.save_document(
            filename=pdf_path.name,
            extraction_mode=args.mode,
            extracted_data=extracted_data,
            status="success",
        )

        print("\n✓ Processing complete!")
        print(f"\nDocument ID: {result.metadata.id}")
        print("\nExtracted Data:")
        print(extracted_data.model_dump_json(indent=2))
        return 0

    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        return 1


def _cmd_eval(args: argparse.Namespace) -> int:
    reports = evaluate_samples(mode=args.mode)
    print_report(reports)

    # report-only: do not fail the process (unless the user explicitly asks later)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Process PDF documents")
    sub = parser.add_subparsers(dest="command")

    # process command (default)
    parser.add_argument("pdf_file", nargs="?", help="Path to PDF file")
    parser.add_argument(
        "--mode",
        choices=["llm", "rules"],
        default="llm",
        help="Extraction mode (default: llm)",
    )

    # eval command
    eval_p = sub.add_parser("eval", help="Evaluate extraction on samples/ (report-only)")
    eval_p.add_argument(
        "--mode",
        choices=["llm", "rules"],
        default="llm",
        help="Extraction mode (default: llm)",
    )

    args = parser.parse_args()

    if args.command == "eval":
        raise SystemExit(_cmd_eval(args))

    if not args.pdf_file:
        parser.print_help()
        raise SystemExit(2)

    raise SystemExit(_cmd_process(args))


if __name__ == "__main__":
    main()
