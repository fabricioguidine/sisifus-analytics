"""Import emails from exported .mbox files (Google Takeout format)"""

import email
from pathlib import Path
from typing import List, Dict, Optional
from tqdm import tqdm
import mailbox

from src.config import INPUT_DIR


class EmailImporter:
    """Import emails from Google Takeout .mbox files"""
    
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
            
            print(f"[SUCCESS] Imported {len(emails)} emails from mbox file")
            return emails
        except Exception as e:
            print(f"Error reading mbox file: {e}")
            return emails
    
    
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
        Automatically detect and import .mbox files from input folder
        Recursively searches for .mbox files (handles Google Takeout folder structure)
        """
        all_emails = []
        
        # Recursively look for .mbox files (handles nested Google Takeout folders)
        print("Searching for .mbox files...")
        mbox_files = list(self.input_dir.rglob("*.mbox"))
        
        if not mbox_files:
            print(f"[INFO] No .mbox files found in {self.input_dir}")
            print("\nTip: Extract your Google Takeout ZIP and place the .mbox file(s) in the input/ folder")
            return all_emails
        
        print(f"[INFO] Found {len(mbox_files)} .mbox file(s)")
        
        # Filter out any .mbox files in configuration/user settings folders
        filtered_mbox_files = []
        for mbox_file in mbox_files:
            # Skip files in configuration/settings folders
            path_str = str(mbox_file).lower()
            if 'configurações' in path_str or 'settings' in path_str or 'user' in path_str:
                continue
            filtered_mbox_files.append(mbox_file)
        
        for mbox_file in filtered_mbox_files:
            print(f"\nFound mbox file: {mbox_file.relative_to(self.input_dir)}")
            emails = self.import_from_mbox(mbox_file)
            all_emails.extend(emails)
        
        return all_emails


