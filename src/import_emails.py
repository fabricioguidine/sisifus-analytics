"""Script to import emails from exported files (Google Takeout, etc.)"""

import sys
import argparse
from pathlib import Path

from src.config import INPUT_DIR
from src.email_importer import EmailImporter
from src.email_storage import EmailStorage


def import_emails(source_path: str = None, format_type: str = None, output_file: str = "emails.json"):
    """Import emails from exported files and save to input folder"""
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
        
        if format_type == "mbox" or (source.suffix == ".mbox"):
            print(f"Importing from mbox file: {source.name}")
            emails = importer.import_from_mbox(source)
        elif format_type == "eml" or source.is_dir():
            print(f"Importing from directory: {source.name}")
            emails = importer.import_from_eml_files(source)
        elif format_type == "json" or (source.suffix == ".json"):
            print(f"Importing from JSON file: {source.name}")
            emails = importer.import_from_json(source)
        else:
            print(f"Unknown format. Trying auto-detect...")
            if source.is_file():
                if source.suffix == ".mbox":
                    emails = importer.import_from_mbox(source)
                elif source.suffix == ".json":
                    emails = importer.import_from_json(source)
                else:
                    print("Error: Unsupported file format")
                    sys.exit(1)
            else:
                emails = importer.import_from_eml_files(source)
    else:
        # Auto-import from input folder
        print("Auto-detecting email files in input folder...")
        emails = importer.auto_import()
    
    if not emails:
        print("\n✗ No emails imported. Please check your files.")
        sys.exit(1)
    
    print(f"\n✓ Total emails imported: {len(emails)}")
    print()
    
    # Save to emails.json
    print(f"Saving to {storage.storage_file}...")
    overwrite = not storage.file_exists()
    if storage.file_exists():
        response = input(f"File {storage.storage_file} exists. Overwrite? (y/n): ").lower()
        overwrite = response == 'y'
    
    success = storage.save_emails(emails, overwrite=overwrite)
    
    if success:
        print(f"✓ Saved {len(emails)} emails to {storage.storage_file}")
        print()
        print("=" * 60)
        print("Import complete!")
        print("=" * 60)
        print()
        print("You can now run the main script to process these emails:")
        print("  python -m src.main --use-input")
    else:
        print("✗ Failed to save emails")
        sys.exit(1)


def main():
    """Main function with command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Import emails from exported files (Google Takeout, mbox, eml, JSON)"
    )
    parser.add_argument(
        "source",
        nargs="?",
        help="Path to mbox file, directory of .eml files, or JSON file. "
             "If not provided, auto-detects in input folder."
    )
    parser.add_argument(
        "--format",
        choices=["mbox", "eml", "json"],
        help="File format (auto-detected if not specified)"
    )
    parser.add_argument(
        "--output",
        default="emails.json",
        help="Output filename (default: emails.json)"
    )
    
    args = parser.parse_args()
    
    import_emails(
        source_path=args.source,
        format_type=args.format,
        output_file=args.output
    )


if __name__ == "__main__":
    main()

