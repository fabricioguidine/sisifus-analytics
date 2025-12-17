"""Main entry point for the application"""

import sys
import argparse
from pathlib import Path
from tqdm import tqdm

from src.config import INPUT_DIR, OUTPUT_DIR
from src.email_parser import EmailParser
from src.email_storage import EmailStorage
from src.classifier import EmailClassifier
from src.analytics import AnalyticsGenerator


def load_emails_from_input() -> list:
    """Load emails from input folder"""
    storage = EmailStorage()
    
    if not storage.file_exists():
        print(f"✗ No emails found in {storage.storage_file}")
        print()
        print("  Options to get emails:")
        print("  1. Extract from email server: python -m src.extract_emails")
        print("  2. Import from exported files: python -m src.import_emails")
        print("     (Supports Google Takeout .mbox files, .eml files, or JSON)")
        return None
    
    print("Loading emails from input folder...")
    emails = storage.load_emails()
    
    if emails:
        metadata = storage.get_metadata()
        print(f"✓ Loaded {len(emails)} emails from {storage.storage_file}")
        if metadata:
            print(f"  Export date: {metadata.get('export_date', 'Unknown')}")
    else:
        print(f"✗ Failed to load emails from {storage.storage_file}")
    
    return emails


def fetch_emails_from_server() -> list:
    """Fetch emails from email server"""
    from src.config import EMAIL_ADDRESS, EMAIL_PASSWORD
    
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print("ERROR: Email credentials not configured!")
        print("Please set EMAIL_ADDRESS and EMAIL_PASSWORD in .env file")
        print("See README.md for security instructions")
        return None
    
    print("Step 1: Connecting to email server...")
    parser = EmailParser()
    
    if not parser.connect():
        print("Failed to connect to email server. Please check your credentials.")
        return None
    
    print("✓ Connected successfully")
    print()
    
    print("Step 2: Fetching job-related emails...")
    emails = parser.fetch_job_related_emails(limit=None)
    parser.disconnect()
    
    if not emails:
        print("No emails found. Please check your search criteria.")
        return None
    
    print(f"✓ Found {len(emails)} job-related emails")
    print()
    
    return emails


def main():
    """Main function to parse emails and generate analytics"""
    parser = argparse.ArgumentParser(
        description="Job Application Email Parser and Analytics"
    )
    parser.add_argument(
        "--use-input",
        action="store_true",
        help="Use emails from input folder instead of fetching from server"
    )
    parser.add_argument(
        "--extract-only",
        action="store_true",
        help="Only extract emails and save to input folder, don't process"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Sisifus Analytics - Job Application Email Parser")
    print("=" * 60)
    print()
    
    # Determine email source
    if args.use_input:
        if args.extract_only:
            print("ERROR: --extract-only cannot be used with --use-input")
            print("Use --extract-only to fetch and save emails, or --use-input to load saved emails.")
            sys.exit(1)
        emails = load_emails_from_input()
        if not emails:
            sys.exit(1)
    else:
        emails = fetch_emails_from_server()
        if not emails:
            sys.exit(1)
        
        # Always save fetched emails to input folder
        print("Saving fetched emails to input folder...")
        storage = EmailStorage()
        storage.save_emails(emails, overwrite=False)
        print(f"✓ Saved to {storage.storage_file}")
        print()
        
        if args.extract_only:
            print("Extraction complete. Use --use-input flag to process these emails.")
            return
    
    
    print("Step 3: Classifying emails...")
    classifier = EmailClassifier()
    
    classified_emails = []
    for email_data in tqdm(emails, desc="Classifying", unit="email"):
        classified = classifier.classify_emails([email_data])
        classified_emails.extend(classified)
    
    print(f"✓ Classified {len(classified_emails)} emails")
    print()
    
    print("Step 4: Generating analytics...")
    analytics = AnalyticsGenerator(classified_emails)
    summary = analytics.save_analytics()
    
    print("✓ Analytics generated")
    print()
    
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total Applications: {summary['total_applications']}")
    print(f"Rejected: {summary['rejected_count']}")
    print(f"Offers: {summary['offers_count']}")
    print(f"Accepted: {summary['accepted_count']}")
    print(f"Interviews: {summary['interviews_count']}")
    print(f"Withdrew: {summary['withdrew_count']}")
    print(f"No Reply: {summary['no_reply_count']}")
    print(f"Total Companies: {summary['total_companies']}")
    print(f"Classification Accuracy: {summary['accuracy_percentage']}%")
    print()
    print("Output files saved to:")
    print(f"  - Analytics JSON: {OUTPUT_DIR / 'analytics.json'}")
    print(f"  - Analytics CSV: {OUTPUT_DIR / 'applications.csv'}")
    print(f"  - Sankey Diagram: {OUTPUT_DIR / 'sankey_diagram.html'}")
    print("=" * 60)


if __name__ == "__main__":
    main()

