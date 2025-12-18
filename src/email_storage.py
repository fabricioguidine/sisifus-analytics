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
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error saving emails: {e}")
            return False
    
    def load_emails(self) -> Optional[List[Dict]]:
        """
        Load emails from JSON file in input folder
        
        Returns:
            List of email dictionaries, or None if file doesn't exist or error occurs
        """
        if not self.storage_file.exists():
            return None
        
        try:
            print(f"Loading emails from {self.storage_file.name}...")
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            emails = data.get("emails", [])
            
            # Convert ISO date strings back to datetime objects
            print(f"Processing {len(emails)} emails...")
            for email_data in tqdm(emails, desc="Loading emails", unit="email"):
                if "date" in email_data and email_data["date"]:
                    try:
                        email_data["date"] = datetime.fromisoformat(email_data["date"])
                    except (ValueError, TypeError):
                        # If parsing fails, keep as string
                        pass
            
            return emails
        except Exception as e:
            print(f"Error loading emails: {e}")
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


