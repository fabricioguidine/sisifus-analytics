"""Main entry point for the application"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from tqdm import tqdm

from src.config import INPUT_DIR, OUTPUT_DIR
from src.email_parser import EmailParser
from src.email_storage import EmailStorage
from src.classifier import EmailClassifier
from src.analytics import AnalyticsGenerator


def filter_emails_by_date(emails: list, months: int = None, year: int = None) -> list:
    """Filter emails by date criteria"""
    if not emails:
        return emails
    
    filtered = []
    now = datetime.now()
    
    for email_data in emails:
        email_date = email_data.get("date")
        
        # Skip if no date
        if not email_date:
            continue
        
        # Convert ISO string to datetime if needed
        if isinstance(email_date, str):
            try:
                email_date = datetime.fromisoformat(email_date.replace('Z', '+00:00'))
            except:
                continue
        
        # Filter by year
        if year is not None:
            if email_date.year != year:
                continue
        
        # Filter by months
        if months is not None:
            cutoff_date = now - relativedelta(months=months)
            if email_date < cutoff_date:
                continue
        
        filtered.append(email_data)
    
    return filtered


def load_emails_from_input(months: int = None, year: int = None) -> list:
    """Load emails from input folder"""
    storage = EmailStorage()
    
    if not storage.file_exists():
        print(f"✗ No emails found in {storage.storage_file}")
        print()
        print("  To import emails, run:")
        print("    python -m src.import_emails")
        print("  This will auto-detect .mbox files in the input/ folder")
        return None
    
    emails = storage.load_emails()
    
    if emails:
        metadata = storage.get_metadata()
        print(f"[SUCCESS] Loaded {len(emails)} emails from {storage.storage_file}")
        if metadata:
            print(f"  Export date: {metadata.get('export_date', 'Unknown')}")
        
        # Apply date filtering
        if months is not None or year is not None:
            original_count = len(emails)
            emails = filter_emails_by_date(emails, months=months, year=year)
            filtered_count = len(emails)
            print(f"[INFO] Filtered to {filtered_count} emails", end="")
            if months:
                print(f" (last {months} months)", end="")
            if year:
                print(f" (year {year})", end="")
            print(f" from {original_count} total")
    else:
        print(f"[ERROR] Failed to load emails from {storage.storage_file}")
    
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
    
    print("[SUCCESS] Connected successfully")
    print()
    
    print("Step 2: Fetching job-related emails...")
    emails = parser.fetch_job_related_emails(limit=None)
    parser.disconnect()
    
    if not emails:
        print("No emails found. Please check your search criteria.")
        return None
    
    print(f"[SUCCESS] Found {len(emails)} job-related emails")
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
    parser.add_argument(
        "--months",
        type=int,
        default=None,
        help="Filter emails from the last X months (e.g., --months 6 for last 6 months)"
    )
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Filter emails from a specific year (e.g., --year 2025)"
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
        emails = load_emails_from_input(months=args.months, year=args.year)
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
        print(f"[SUCCESS] Saved to {storage.storage_file}")
        print()
        
        if args.extract_only:
            print("Extraction complete. Use --use-input flag to process these emails.")
            return
    
    
    print("Step 3: Classifying emails...")
    print(f"[INFO] Classifying {len(emails)} emails...")
    classifier = EmailClassifier()
    
    classified_emails = []
    error_count = 0
    
    # Batch process for better performance (1000 emails at a time)
    BATCH_SIZE = 1000
    total_batches = (len(emails) + BATCH_SIZE - 1) // BATCH_SIZE
    
    print(f"[INFO] Processing in batches of {BATCH_SIZE} emails ({total_batches} batches)")
    
    try:
        for batch_idx in tqdm(range(0, len(emails), BATCH_SIZE), desc="Classifying batches", total=total_batches, unit="batch"):
            batch = emails[batch_idx:batch_idx + BATCH_SIZE]
            try:
                classified = classifier.classify_emails(batch)
                classified_emails.extend(classified)
            except Exception as e:
                # If batch fails, process individually
                if error_count == 0:
                    print(f"\n[WARNING] Batch processing failed, processing individually: {str(e)[:100]}")
                for email_data in batch:
                    try:
                        classified = classifier.classify_emails([email_data])
                        classified_emails.extend(classified)
                    except Exception as inner_e:
                        error_count += 1
                        if error_count <= 5:
                            print(f"\n[WARNING] Error classifying email: {str(inner_e)[:100]}")
                        continue
    except KeyboardInterrupt:
        print(f"\n[INFO] Classification interrupted by user")
        print(f"[INFO] Successfully classified {len(classified_emails)} emails before interruption")
    except Exception as e:
        print(f"\n[ERROR] Error during classification: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"[SUCCESS] Classified {len(classified_emails)} emails")
    if error_count > 0:
        print(f"[INFO] {error_count} emails had classification errors")
    print()
    
    print("Step 4: Generating analytics...")
    analytics = AnalyticsGenerator(classified_emails)
    summary = analytics.save_analytics()
    
    print("[SUCCESS] Analytics generated")
    print()
    
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    if args.months:
        print(f"Date Filter: Last {args.months} months")
    if args.year:
        print(f"Date Filter: Year {args.year}")
    if args.months or args.year:
        print("-" * 60)
    print(f"Total Job-Related Emails: {summary['total_applications']}")
    print(f"Rejected: {summary['rejected_count']}")
    print(f"Offers: {summary['offers_count']}")
    print(f"Accepted: {summary['accepted_count']}")
    print(f"Interviews: {summary['interviews_count']}")
    print(f"Withdrew: {summary['withdrew_count']}")
    print(f"No Reply (Job-related): {summary['no_reply_count']}")
    print(f"Not Job-Related: {summary.get('not_job_related_count', 0)}")
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

