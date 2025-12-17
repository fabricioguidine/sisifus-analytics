"""Email parsing module with IMAP support"""

import imaplib
from email.message import Message
from email.header import decode_header
from email.utils import parsedate_to_datetime
from email import message_from_bytes
from typing import List, Dict, Optional
from datetime import datetime
import ssl
from tqdm import tqdm
from bs4 import BeautifulSoup

from src.config import EMAIL_ADDRESS, EMAIL_PASSWORD, IMAP_SERVER, IMAP_PORT


class EmailParser:
    """Parses emails from IMAP server with secure connection"""
    
    def __init__(self, email_address: str = None, password: str = None, 
                 imap_server: str = None, imap_port: int = None):
        self.email_address = email_address or EMAIL_ADDRESS
        self.password = password or EMAIL_PASSWORD
        self.imap_server = imap_server or IMAP_SERVER
        self.imap_port = imap_port or IMAP_PORT
        self.imap = None
    
    def connect(self) -> bool:
        """Establish secure IMAP connection"""
        try:
            # Create SSL context for secure connection
            context = ssl.create_default_context()
            self.imap = imaplib.IMAP4_SSL(self.imap_server, self.imap_port, ssl_context=context)
            self.imap.login(self.email_address, self.password)
            return True
        except Exception as e:
            print(f"Error connecting to email: {e}")
            return False
    
    def disconnect(self):
        """Close IMAP connection"""
        if self.imap:
            try:
                self.imap.close()
                self.imap.logout()
            except:
                pass
    
    def _decode_header(self, header_value: str) -> str:
        """Decode email header"""
        if not header_value:
            return ""
        decoded = decode_header(header_value)
        parts = []
        for part, encoding in decoded:
            if isinstance(part, bytes):
                parts.append(part.decode(encoding or 'utf-8', errors='ignore'))
            else:
                parts.append(part)
        return "".join(parts)
    
    def _extract_text_from_html(self, html_content: str) -> str:
        """Extract plain text from HTML email"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'lxml')
        return soup.get_text(separator=' ', strip=True)
    
    def _parse_email_body(self, msg: Message) -> str:
        """Extract text body from email"""
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body += payload.decode('utf-8', errors='ignore')
                elif content_type == "text/html":
                    payload = part.get_payload(decode=True)
                    if payload:
                        html_content = payload.decode('utf-8', errors='ignore')
                        body += self._extract_text_from_html(html_content)
        else:
            content_type = msg.get_content_type()
            payload = msg.get_payload(decode=True)
            if payload:
                if content_type == "text/html":
                    body = self._extract_text_from_html(
                        payload.decode('utf-8', errors='ignore')
                    )
                else:
                    body = payload.decode('utf-8', errors='ignore')
        return body
    
    def fetch_emails(self, search_criteria: str = "ALL", limit: Optional[int] = None) -> List[Dict]:
        """Fetch emails from mailbox"""
        if not self.imap:
            if not self.connect():
                return []
        
        try:
            self.imap.select("INBOX")
            _, message_numbers = self.imap.search(None, search_criteria)
            
            email_ids = message_numbers[0].split()
            if limit:
                email_ids = email_ids[:limit]
            
            emails = []
            total = len(email_ids)
            
            for num in tqdm(email_ids, desc="Fetching emails", unit="email"):
                try:
                    _, msg_data = self.imap.fetch(num, "(RFC822)")
                    msg = message_from_bytes(msg_data[0][1])
                    
                    subject = self._decode_header(msg["Subject"] or "")
                    from_addr = self._decode_header(msg["From"] or "")
                    date_str = msg["Date"]
                    date = None
                    if date_str:
                        try:
                            date = parsedate_to_datetime(date_str)
                        except:
                            pass
                    
                    body = self._parse_email_body(msg)
                    
                    emails.append({
                        "id": num.decode() if isinstance(num, bytes) else str(num),
                        "subject": subject,
                        "from": from_addr,
                        "date": date,
                        "body": body,
                        "raw_date": date_str
                    })
                except Exception as e:
                    print(f"Error parsing email {num}: {e}")
                    continue
            
            return emails
        except Exception as e:
            print(f"Error fetching emails: {e}")
            return []
    
    def fetch_job_related_emails(self, keywords: List[str] = None, limit: Optional[int] = None) -> List[Dict]:
        """Fetch emails related to job applications"""
        if keywords is None:
            keywords = ["job", "application", "interview", "recruiter", "hiring", 
                       "position", "candidate", "opportunity", "apply", "career"]
        
        # Build search query
        search_query = " OR ".join([f'(BODY "{keyword}")' for keyword in keywords])
        search_query += " OR " + " OR ".join([f'(SUBJECT "{keyword}")' for keyword in keywords])
        
        # Fetch emails
        emails = self.fetch_emails(search_criteria=f"({search_query})", limit=limit)
        return emails

