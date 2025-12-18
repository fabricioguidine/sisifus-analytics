"""Import emails from exported .mbox files (Google Takeout format)"""

import email
from pathlib import Path
from typing import List, Dict, Optional
from tqdm import tqdm
import mailbox
from datetime import datetime

from src.config import INPUT_DIR


class EmailImporter:
    """Import emails from Google Takeout .mbox files"""
    
    def __init__(self, input_dir: Path = None):
        self.input_dir = input_dir or INPUT_DIR
        self.input_dir.mkdir(exist_ok=True)
    
    def import_from_mbox(self, mbox_path: Path, timeout_minutes: int = 30) -> List[Dict]:
        """
        Import emails from mbox file (Google Takeout format)
        
        Args:
            mbox_path: Path to .mbox file
            timeout_minutes: Maximum time to wait (default: 30 minutes)
        
        Returns:
            List of email dictionaries
        """
        emails = []
        start_time = datetime.now()
        
        if not mbox_path.exists():
            print(f"[ERROR] File not found: {mbox_path}")
            return emails
        
        try:
            print(f"[INFO] Opening mbox file: {mbox_path.name}")
            print(f"[INFO] This may take several minutes for large files...")
            mbox = mailbox.mbox(str(mbox_path))
            total = len(mbox)
            
            if total == 0:
                print(f"[WARNING] Mbox file appears to be empty")
                return emails
            
            print(f"[INFO] Found {total} emails in file")
            print(f"[INFO] Starting import (timeout: {timeout_minutes} minutes)...")
            
            imported_count = 0
            error_count = 0
            
            for msg in tqdm(mbox, desc=f"Importing from {mbox_path.name}", total=total, unit="email"):
                # Check for timeout
                elapsed = (datetime.now() - start_time).total_seconds() / 60
                if elapsed > timeout_minutes:
                    print(f"\n[WARNING] Timeout reached ({timeout_minutes} minutes)")
                    print(f"[INFO] Imported {imported_count} emails before timeout")
                    print(f"[INFO] You can continue importing later - the process will skip already imported emails")
                    break
                
                try:
                    email_data = self._parse_message(msg)
                    if email_data:
                        emails.append(email_data)
                        imported_count += 1
                except Exception as e:
                    error_count += 1
                    if error_count <= 5:  # Only show first 5 errors
                        print(f"\n[WARNING] Error parsing email {imported_count + error_count}: {str(e)[:100]}")
                    continue
            
            elapsed_time = (datetime.now() - start_time).total_seconds()
            print(f"\n[SUCCESS] Imported {len(emails)} emails from mbox file in {elapsed_time:.1f} seconds")
            if error_count > 0:
                print(f"[INFO] {error_count} emails had parsing errors and were skipped")
            
            return emails
        except KeyboardInterrupt:
            print(f"\n[INFO] Import interrupted by user")
            print(f"[INFO] Imported {len(emails)} emails before interruption")
            return emails
        except Exception as e:
            print(f"\n[ERROR] Error reading mbox file: {type(e).__name__}: {e}")
            print(f"[INFO] Successfully imported {len(emails)} emails before error occurred")
            import traceback
            print(f"[DEBUG] Full error traceback:")
            traceback.print_exc()
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
        # Only filter if they're in a subdirectory that looks like a settings folder
        filtered_mbox_files = []
        for mbox_file in mbox_files:
            # Skip files only if they're in a configuration/settings folder path
            # Check folder structure, not filename
            path_parts = [p.lower() for p in mbox_file.parts[:-1]]  # Exclude filename itself
            
            # Check if any parent directory is a settings folder
            is_in_settings_folder = False
            for part in path_parts:
                # Only match exact folder names that indicate settings/config folders
                if part in ['configurações do usuário', 'user settings', 'user settings folder']:
                    is_in_settings_folder = True
                    break
            
            if not is_in_settings_folder:
                filtered_mbox_files.append(mbox_file)
            else:
                print(f"[INFO] Skipping file in settings folder: {mbox_file.relative_to(self.input_dir)}")
        
        if not filtered_mbox_files:
            print(f"[WARNING] No valid .mbox files found after filtering")
            return all_emails
        
        for mbox_file in filtered_mbox_files:
            print(f"\n[INFO] Processing mbox file: {mbox_file.relative_to(self.input_dir)}")
            try:
                file_emails = self.import_from_mbox(mbox_file)
                all_emails.extend(file_emails)
                if len(file_emails) == 0:
                    print(f"[WARNING] No emails were imported from {mbox_file.name}")
            except KeyboardInterrupt:
                print(f"\n[INFO] Import process interrupted by user")
                print(f"[INFO] Successfully imported {len(all_emails)} emails before interruption")
                break
            except Exception as e:
                print(f"\n[ERROR] Failed to import from {mbox_file.name}: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        return all_emails


