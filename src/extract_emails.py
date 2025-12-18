"""Script to extract emails from email server and save to input folder"""

import sys
import argparse
from pathlib import Path

from src.config import EMAIL_ADDRESS, EMAIL_PASSWORD
from src.email_parser import EmailParser
from src.email_storage import EmailStorage


def extract_emails(limit: int = None, overwrite: bool = True):
    """Extract emails from email server and save to input folder"""
    print("=" * 60)
    print("Email Extraction Tool")
    print("=" * 60)
    print()
    
    # Check if email credentials are set
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print("ERROR: Email credentials not configured!")
        print("Please set EMAIL_ADDRESS and EMAIL_PASSWORD in .env file")
        print("See README.md for security instructions")
        sys.exit(1)
    
    print("Step 1: Connecting to email server...")
    parser = EmailParser()
    
    if not parser.connect():
        print("Failed to connect to email server. Please check your credentials.")
        sys.exit(1)
    
    print("✓ Connected successfully")
    print()
    
    print("Step 2: Fetching job-related emails...")
    emails = parser.fetch_job_related_emails(limit=limit)
    parser.disconnect()
    
    if not emails:
        print("No emails found. Please check your search criteria.")
        sys.exit(1)
    
    print(f"✓ Found {len(emails)} job-related emails")
    print()
    
    print("Step 3: Saving emails to input folder...")
    storage = EmailStorage()
    
    if storage.file_exists() and not overwrite:
        print(f"⚠ Warning: File {storage.storage_file} already exists.")
        response = input("Append to existing file? (y/n): ").lower()
        if response != 'y':
            overwrite = True
    
    success = storage.save_emails(emails, overwrite=overwrite)
    
    if success:
        print(f"✓ Saved {len(emails)} emails to {storage.storage_file}")
        metadata = storage.get_metadata()
        if metadata:
            print(f"  Export date: {metadata.get('export_date', 'Unknown')}")
            print(f"  Total emails in file: {metadata.get('total_emails', len(emails))}")
    else:
        print("✗ Failed to save emails")
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("Extraction complete!")
    print("=" * 60)
    print()
    print("You can now run the main script to process these emails:")
    print("  python -m src.main --use-input")
    print()


def main():
    """Main function with command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Extract emails from email server and save to input folder"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of emails to fetch (default: all)"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=True,
        help="Overwrite existing file (default: True)"
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to existing file instead of overwriting"
    )
    
    args = parser.parse_args()
    
    overwrite = not args.append
    extract_emails(limit=args.limit, overwrite=overwrite)


if __name__ == "__main__":
    main()


