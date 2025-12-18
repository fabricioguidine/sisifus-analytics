"""Script to import emails from exported files (Google Takeout, etc.)"""

import sys
import argparse
from pathlib import Path

from src.config import INPUT_DIR
from src.email_importer import EmailImporter
from src.email_storage import EmailStorage


def import_emails(source_path: str = None, format_type: str = None, output_file: str = "emails.json"):
    """
    Import emails from .mbox file and save to input folder
    
    Args:
        source_path: Path to .mbox file (optional, auto-detects if not provided)
        format_type: Not used (kept for compatibility)
        output_file: Output filename (default: emails.json)
    """
    print("=" * 60)
    print("Email Import Tool")
    print("=" * 60)
    print()
    
    importer = EmailImporter()
    storage = EmailStorage(storage_file=output_file)
    
    emails = []
    
    if source_path:
        # Import from specific file/directory
        source = Path(source_path)
        if not source.exists():
            print(f"Error: Path not found: {source_path}")
            sys.exit(1)
        
        if source.suffix == ".mbox":
            print(f"Importing from mbox file: {source.name}")
            emails = importer.import_from_mbox(source)
        elif source.is_dir():
            print("Error: Directories are not supported. Please specify the .mbox file path.")
            sys.exit(1)
        else:
            print(f"Error: Unsupported file format. Only .mbox files are supported.")
            sys.exit(1)
    else:
        # Auto-import from input folder
        print("Auto-detecting .mbox files in input folder...")
        print("(This may take a moment if you have many files)")
        emails = importer.auto_import()
    
    if not emails:
        print("\n[ERROR] No emails imported. Please check your files.")
        sys.exit(1)
    
    print(f"\n[SUCCESS] Total emails imported: {len(emails)}")
    print()
    
    # Save to emails.json
    print(f"Saving to {storage.storage_file}...")
    overwrite = not storage.file_exists()
    if storage.file_exists():
        response = input(f"File {storage.storage_file} exists. Overwrite? (y/n): ").lower()
        overwrite = response == 'y'
    
    success = storage.save_emails(emails, overwrite=overwrite)
    
    if success:
        print(f"[SUCCESS] Saved {len(emails)} emails to {storage.storage_file}")
        print()
        print("=" * 60)
        print("Import complete!")
        print("=" * 60)
        print()
        print("You can now run the main script to process these emails:")
        print("  python -m src.main --use-input")
    else:
        print("[ERROR] Failed to save emails")
        sys.exit(1)


def main():
    """Main function with command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Import emails from Google Takeout .mbox files"
    )
    parser.add_argument(
        "source",
        nargs="?",
        help="Path to .mbox file. If not provided, auto-detects .mbox files in input folder."
    )
    parser.add_argument(
        "--output",
        default="emails.json",
        help="Output filename (default: emails.json)"
    )
    
    args = parser.parse_args()
    
    import_emails(
        source_path=args.source,
        format_type=None,
        output_file=args.output
    )


if __name__ == "__main__":
    main()


