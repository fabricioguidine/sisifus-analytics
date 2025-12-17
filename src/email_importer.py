"""Import emails from exported files (Google Takeout, mbox, eml files)"""

import json
import email
from email import message_from_file, message_from_string
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from tqdm import tqdm
import mailbox
import os

from src.config import INPUT_DIR


class EmailImporter:
    """Import emails from various exported formats"""
    
    def __init__(self, input_dir: Path = None):
        self.input_dir = input_dir or INPUT_DIR
        self.input_dir.mkdir(exist_ok=True)
    
    def import_from_mbox(self, mbox_path: Path) -> List[Dict]:
        """Import emails from mbox file (Google Takeout format)"""
        emails = []
        
        if not mbox_path.exists():
            print(f"Error: File not found: {mbox_path}")
            return emails
        
        try:
            mbox = mailbox.mbox(str(mbox_path))
            total = len(mbox)
            
            for msg in tqdm(mbox, desc=f"Importing from {mbox_path.name}", total=total, unit="email"):
                email_data = self._parse_message(msg)
                if email_data:
                    emails.append(email_data)
            
            print(f"✓ Imported {len(emails)} emails from mbox file")
            return emails
        except Exception as e:
            print(f"Error reading mbox file: {e}")
            return emails
    
    def import_from_eml_files(self, eml_dir: Path) -> List[Dict]:
        """Import emails from directory of .eml files"""
        emails = []
        
        if not eml_dir.exists() or not eml_dir.is_dir():
            print(f"Error: Directory not found: {eml_dir}")
            return emails
        
        eml_files = list(eml_dir.glob("*.eml"))
        if not eml_files:
            print(f"No .eml files found in {eml_dir}")
            return emails
        
        for eml_file in tqdm(eml_files, desc=f"Importing .eml files", unit="file"):
            try:
                with open(eml_file, 'r', encoding='utf-8', errors='ignore') as f:
                    msg = message_from_file(f)
                    email_data = self._parse_message(msg)
                    if email_data:
                        emails.append(email_data)
            except Exception as e:
                print(f"Error reading {eml_file.name}: {e}")
                continue
        
        print(f"✓ Imported {len(emails)} emails from .eml files")
        return emails
    
    def import_from_json(self, json_path: Path) -> List[Dict]:
        """Import emails from JSON file"""
        if not json_path.exists():
            print(f"Error: File not found: {json_path}")
            return []
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                emails = data
            elif isinstance(data, dict) and "emails" in data:
                emails = data["emails"]
            else:
                print("Error: Invalid JSON structure")
                return []
            
            # Convert date strings to datetime if needed
            for email_data in emails:
                if "date" in email_data and email_data["date"]:
                    if isinstance(email_data["date"], str):
                        try:
                            email_data["date"] = datetime.fromisoformat(email_data["date"])
                        except (ValueError, TypeError):
                            pass
            
            print(f"✓ Imported {len(emails)} emails from JSON file")
            return emails
        except Exception as e:
            print(f"Error reading JSON file: {e}")
            return []
    
    def _parse_message(self, msg: email.message.Message) -> Optional[Dict]:
        """Parse email message object into dictionary"""
        try:
            # Extract headers
            subject = self._decode_header(msg.get("Subject", ""))
            from_addr = self._decode_header(msg.get("From", ""))
            date_str = msg.get("Date", "")
            
            # Parse date
            date = None
            if date_str:
                try:
                    from email.utils import parsedate_to_datetime
                    date = parsedate_to_datetime(date_str)
                except:
                    pass
            
            # Extract body
            body = self._extract_body(msg)
            
            # Generate a unique ID from headers
            msg_id = msg.get("Message-ID", f"{subject}_{date_str}_{from_addr}")
            if isinstance(msg_id, bytes):
                msg_id = msg_id.decode('utf-8', errors='ignore')
            
            return {
                "id": msg_id[:100],  # Limit ID length
                "subject": subject,
                "from": from_addr,
                "date": date,
                "body": body,
                "raw_date": date_str
            }
        except Exception as e:
            print(f"Error parsing message: {e}")
            return None
    
    def _decode_header(self, header_value: str) -> str:
        """Decode email header"""
        if not header_value:
            return ""
        from email.header import decode_header
        decoded = decode_header(header_value)
        parts = []
        for part, encoding in decoded:
            if isinstance(part, bytes):
                parts.append(part.decode(encoding or 'utf-8', errors='ignore'))
            else:
                parts.append(part)
        return "".join(parts)
    
    def _extract_body(self, msg: email.message.Message) -> str:
        """Extract text body from email message"""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        try:
                            body += payload.decode('utf-8', errors='ignore')
                        except:
                            body += str(payload)
                elif content_type == "text/html":
                    # Extract text from HTML if no plain text found
                    if not body:
                        payload = part.get_payload(decode=True)
                        if payload:
                            try:
                                html_content = payload.decode('utf-8', errors='ignore')
                                from bs4 import BeautifulSoup
                                soup = BeautifulSoup(html_content, 'lxml')
                                body = soup.get_text(separator=' ', strip=True)
                            except:
                                pass
        else:
            content_type = msg.get_content_type()
            payload = msg.get_payload(decode=True)
            if payload:
                if content_type == "text/html":
                    try:
                        from bs4 import BeautifulSoup
                        html_content = payload.decode('utf-8', errors='ignore')
                        soup = BeautifulSoup(html_content, 'lxml')
                        body = soup.get_text(separator=' ', strip=True)
                    except:
                        body = payload.decode('utf-8', errors='ignore')
                else:
                    body = payload.decode('utf-8', errors='ignore')
        
        return body
    
    def auto_import(self) -> List[Dict]:
        """
        Automatically detect and import emails from input folder
        Looks for: .mbox files, .eml files, emails.json
        """
        all_emails = []
        
        # Look for mbox files
        mbox_files = list(self.input_dir.glob("*.mbox"))
        for mbox_file in mbox_files:
            print(f"\nFound mbox file: {mbox_file.name}")
            emails = self.import_from_mbox(mbox_file)
            all_emails.extend(emails)
        
        # Look for eml files (in a subdirectory or root)
        eml_dirs = [self.input_dir]
        # Also check for common Google Takeout structure
        for subdir in self.input_dir.iterdir():
            if subdir.is_dir() and subdir.name.lower() in ['mail', 'emails', 'messages']:
                eml_dirs.append(subdir)
        
        for eml_dir in eml_dirs:
            eml_files = list(eml_dir.glob("*.eml"))
            if eml_files:
                print(f"\nFound {len(eml_files)} .eml files in {eml_dir.name}")
                emails = self.import_from_eml_files(eml_dir)
                all_emails.extend(emails)
        
        # Look for JSON file (but not emails.json which is our output format)
        json_files = [f for f in self.input_dir.glob("*.json") 
                     if f.name != "emails.json"]
        for json_file in json_files:
            print(f"\nFound JSON file: {json_file.name}")
            emails = self.import_from_json(json_file)
            all_emails.extend(emails)
        
        return all_emails

