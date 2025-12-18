"""Email data storage and retrieval from input folder"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from tqdm import tqdm

from src.config import INPUT_DIR


class EmailStorage:
    """Handles saving and loading emails to/from input folder"""
    
    def __init__(self, storage_file: str = "emails.json"):
        """Initialize email storage"""
        INPUT_DIR.mkdir(exist_ok=True)
        self.storage_file = INPUT_DIR / storage_file
    
    def save_emails(self, emails: List[Dict], overwrite: bool = True) -> bool:
        """
        Save emails to JSON file in input folder
        
        Args:
            emails: List of email dictionaries to save
            overwrite: If True, overwrite existing file. If False, append.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert datetime objects to ISO format strings for JSON serialization
            emails_to_save = []
            for email_data in tqdm(emails, desc="Saving emails", unit="email"):
                email_dict = email_data.copy()
                
                # Convert date to ISO string if it's a datetime object
                if "date" in email_dict and email_dict["date"]:
                    if isinstance(email_dict["date"], datetime):
                        email_dict["date"] = email_dict["date"].isoformat()
                
                emails_to_save.append(email_dict)
            
            # Prepare data structure
            data = {
                "metadata": {
                    "export_date": datetime.now().isoformat(),
                    "total_emails": len(emails_to_save),
                    "source": "email_fetch"
                },
                "emails": emails_to_save
            }
            
            # Load existing data if appending
            if not overwrite and self.storage_file.exists():
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    existing_emails = existing_data.get("emails", [])
                    
                    # Merge emails (avoid duplicates by ID)
                    existing_ids = {email.get("id") for email in existing_emails}
                    new_emails = [
                        email for email in emails_to_save 
                        if email.get("id") not in existing_ids
                    ]
                    emails_to_save = existing_emails + new_emails
                    data["emails"] = emails_to_save
                    data["metadata"]["total_emails"] = len(emails_to_save)
            
            # Save to file
            print(f"[INFO] Writing {len(emails_to_save)} emails to file...")
            try:
                with open(self.storage_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"[SUCCESS] File saved successfully")
                return True
            except Exception as write_error:
                print(f"[ERROR] Error writing to file: {write_error}")
                import traceback
                traceback.print_exc()
                return False
        except KeyboardInterrupt:
            print(f"\n[ERROR] Save operation interrupted by user")
            raise
        except Exception as e:
            print(f"[ERROR] Error saving emails: {e}")
            print(f"[ERROR] Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_emails(self, months: int = None, year: int = None) -> Optional[List[Dict]]:
        """
        Load emails from JSON file in input folder with optional date filtering
        
        Args:
            months: Filter to last N months (None = no filter)
            year: Filter to specific year (None = no filter)
        
        Returns:
            List of email dictionaries, or None if file doesn't exist or error occurs
        """
        if not self.storage_file.exists():
            return None
        
        try:
            print(f"[INFO] Loading emails from {self.storage_file.name}...")
            file_size = self.storage_file.stat().st_size / (1024*1024)
            print(f"[INFO] File size: {file_size:.2f} MB")
            
            if months is not None or year is not None:
                filter_desc = []
                if year:
                    filter_desc.append(f"year {year}")
                if months:
                    filter_desc.append(f"last {months} months")
                print(f"[INFO] Filtering emails: {', '.join(filter_desc)}")
            
            print("[INFO] Reading JSON file...")
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            all_emails = data.get("emails", [])
            print(f"[INFO] Found {len(all_emails)} emails in file")
            
            if len(all_emails) == 0:
                print("[WARNING] No emails found in file")
                return []
            
            # Filter emails during loading if date criteria provided
            now = datetime.now()
            from dateutil.relativedelta import relativedelta
            
            emails = []
            cutoff_date = None
            if months is not None:
                cutoff_date = now - relativedelta(months=months)
            
            print("[INFO] Processing and filtering emails...")
            processed_count = 0
            error_count = 0
            filtered_out = 0
            
            for email_data in tqdm(all_emails, desc="Loading emails", unit="email"):
                try:
                    # Convert date string to datetime
                    email_date = None
                    if "date" in email_data and email_data["date"]:
                        try:
                            if isinstance(email_data["date"], str):
                                email_data["date"] = datetime.fromisoformat(email_data["date"].replace('Z', '+00:00'))
                            email_date = email_data["date"]
                        except (ValueError, TypeError):
                            # If parsing fails, skip date filtering for this email
                            pass
                    
                    # Apply date filtering if criteria provided
                    if email_date:
                        # Filter by year
                        if year is not None and email_date.year != year:
                            filtered_out += 1
                            continue
                        
                        # Filter by months
                        if cutoff_date and email_date < cutoff_date:
                            filtered_out += 1
                            continue
                    elif (months is not None or year is not None):
                        # If we have date filters but email has no valid date, skip it
                        filtered_out += 1
                        continue
                    
                    emails.append(email_data)
                    processed_count += 1
                except Exception as e:
                    error_count += 1
                    if error_count <= 5:
                        print(f"\n[WARNING] Error processing email: {e}")
                    continue
            
            if filtered_out > 0:
                print(f"[INFO] Filtered out {filtered_out} emails based on date criteria")
            
            if error_count > 0:
                print(f"\n[WARNING] {error_count} emails had processing errors")
            
            print(f"[SUCCESS] Loaded {len(emails)} emails (from {len(all_emails)} total)")
            
            return emails
            
        except KeyboardInterrupt:
            print(f"\n[ERROR] Load operation interrupted by user")
            raise
        except FileNotFoundError:
            print(f"[ERROR] File not found: {self.storage_file}")
            return None
        except json.JSONDecodeError as e:
            print(f"[ERROR] Invalid JSON file: {e}")
            print(f"[ERROR] The file may be corrupted")
            return None
        except Exception as e:
            print(f"[ERROR] Error loading emails: {e}")
            print(f"[ERROR] Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_metadata(self) -> Optional[Dict]:
        """Get metadata from stored emails file"""
        if not self.storage_file.exists():
            return None
        
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get("metadata")
        except Exception as e:
            print(f"Error reading metadata: {e}")
            return None
    
    def file_exists(self) -> bool:
        """Check if storage file exists"""
        return self.storage_file.exists()
    
    def delete_storage(self) -> bool:
        """Delete the storage file"""
        try:
            if self.storage_file.exists():
                self.storage_file.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error deleting storage file: {e}")
            return False


