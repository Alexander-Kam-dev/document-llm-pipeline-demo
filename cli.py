"""CLI tool for processing PDFs."""
import sys
import argparse
from pathlib import Path
from app.pipeline import process_document
from app.storage import storage


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Process PDF documents")
    parser.add_argument("pdf_file", help="Path to PDF file")
    parser.add_argument("--mode", choices=["llm", "rules"], default="llm",
                       help="Extraction mode (default: llm)")
    
    args = parser.parse_args()
    
    # Read PDF file
    pdf_path = Path(args.pdf_file)
    if not pdf_path.exists():
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)
    
    if not pdf_path.suffix.lower() == '.pdf':
        print(f"Error: File must be a PDF")
        sys.exit(1)
    
    print(f"Processing: {pdf_path}")
    print(f"Mode: {args.mode}")
    print("-" * 50)
    
    try:
        # Process document
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        
        extracted_data = process_document(pdf_bytes, mode=args.mode)
        
        # Save to storage
        result = storage.save_document(
            filename=pdf_path.name,
            extraction_mode=args.mode,
            extracted_data=extracted_data,
            status="success"
        )
        
        # Display results
        print("\n✓ Processing complete!")
        print(f"\nDocument ID: {result.metadata.id}")
        print(f"\nExtracted Data:")
        print(extracted_data.model_dump_json(indent=2))
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
