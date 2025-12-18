"""Email classification logic using keyword-based matching (no LLM)"""

import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class EmailClassifier:
    """
    Classifies emails into job application statuses using keyword matching.
    
    Status categories:
    - applied: Initial application sent
    - confirmation: Confirmation of application received
    - interview_1, interview_2, interview_3, etc.: Interview stages
    - offer: Job offer received
    - accepted: Offer accepted
    - rejected: Application rejected
    - withdrew: Application withdrawn
    - no_reply: No response
    """
    
    # Keyword patterns for each status (case-insensitive)
    STATUS_KEYWORDS = {
        "applied": [
            r"application.*submitted",
            r"application.*received",
            r"thank.*for.*your.*application",
            r"we.*received.*your.*application",
            r"application.*sent",
            r"applied.*for",
        ],
        "confirmation": [
            r"confirmation.*application",
            r"application.*confirm",
            r"we.*have.*received.*application",
            r"application.*successfully.*received",
            r"confirm.*receipt.*application",
        ],
        "interview_1": [
            r"first.*interview",
            r"initial.*interview",
            r"screening.*interview",
            r"phone.*screen",
            r"phone.*interview",
            r"video.*screen",
            r"video.*interview",
            r"preliminary.*interview",
            r"first.*round",
            r"round.*1.*interview",
        ],
        "interview_2": [
            r"second.*interview",
            r"next.*round.*interview",
            r"second.*round",
            r"round.*2.*interview",
            r"technical.*interview",
            r"panel.*interview",
        ],
        "interview_3": [
            r"third.*interview",
            r"final.*interview",
            r"round.*3.*interview",
            r"third.*round",
            r"onsite.*interview",
            r"on-site.*interview",
        ],
        "interview_4": [
            r"fourth.*interview",
            r"round.*4.*interview",
            r"fourth.*round",
        ],
        "interview_5": [
            r"fifth.*interview",
            r"round.*5.*interview",
            r"fifth.*round",
        ],
        "offer": [
            r"job.*offer",
            r"offer.*position",
            r"pleased.*to.*offer",
            r"delighted.*to.*offer",
            r"excited.*to.*offer",
            r"offer.*employment",
            r"offer.*you.*position",
            r"extend.*offer",
            r"making.*offer",
        ],
        "accepted": [
            r"accept.*offer",
            r"accepted.*position",
            r"excited.*to.*join",
            r"looking.*forward.*to.*join",
            r"accept.*job",
            r"acceptance.*offer",
        ],
        "rejected": [
            r"not.*moving.*forward",
            r"not.*move.*forward",
            r"decided.*not.*move.*forward",
            r"will.*not.*move.*forward",
            r"unfortunately.*not.*selected",
            r"not.*selected",
            r"regret.*inform",
            r"regret.*to.*inform",
            r"not.*proceed",
            r"decided.*pursue",
            r"other.*candidates",
            r"better.*fit",
            r"not.*right.*fit",
            r"rejection",
            r"we.*decided.*not.*to.*proceed",
            r"we.*decided.*not.*proceed",
            r"not.*advancing",
            r"will.*not.*be.*moving.*forward",
            r"we.*will.*not.*be.*moving.*forward",
        ],
        "withdrew": [
            r"withdraw.*application",
            r"application.*withdrawn",
            r"no.*longer.*interested",
            r"decided.*to.*withdraw",
            r"withdrawing.*application",
        ],
    }
    
    def __init__(self):
        # Compile regex patterns for performance
        self.compiled_patterns = {}
        for status, patterns in self.STATUS_KEYWORDS.items():
            self.compiled_patterns[status] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
    
    def classify_email(self, subject: str, body: str, from_address: str = "") -> Tuple[str, float]:
        """
        Classify email into a status category.
        
        Returns:
            Tuple of (status, confidence_score)
            confidence_score is between 0.0 and 1.0
        """
        # Optimize: Limit body length for performance (first 5000 chars should be enough)
        body_preview = body[:5000].lower() if body else ""
        subject_lower = subject.lower() if subject else ""
        from_lower = from_address.lower() if from_address else ""
        
        # Combine text (prioritize subject and from, then body preview)
        text = f"{subject_lower} {from_lower} {body_preview}"
        
        scores = {}
        
        # Check each status category
        for status, patterns in self.compiled_patterns.items():
            score = 0.0
            matches = 0
            
            for pattern in patterns:
                if pattern.search(text):
                    matches += 1
                    # Early exit for high-confidence matches
                    if matches >= 3:
                        break
            
            # Calculate confidence score
            # More matches = higher confidence
            if matches > 0:
                score = min(1.0, 0.3 + (matches * 0.2))
                
                # Boost score if found in subject (check subject directly, already lowercased)
                if subject_lower and any(pattern.search(subject_lower) for pattern in patterns):
                    score = min(1.0, score + 0.2)
            
            scores[status] = score
        
        # Handle special cases and priority rules
        # Rejection overrides other statuses (high priority)
        # Lower threshold for rejection to catch more cases
        if scores.get("rejected", 0) > 0.3:
            return ("rejected", scores["rejected"])
        
        # Accepted overrides interview stages
        if scores.get("accepted", 0) > 0.5:
            return ("accepted", scores["accepted"])
        
        # Offer overrides interview stages
        if scores.get("offer", 0) > 0.5:
            return ("offer", scores["offer"])
        
        # Withdrew overrides most statuses
        if scores.get("withdrew", 0) > 0.5:
            return ("withdrew", scores["withdrew"])
        
        # Interview stages (check highest first)
        for i in range(5, 0, -1):
            status = f"interview_{i}"
            if scores.get(status, 0) > 0.4:
                return (status, scores[status])
        
        # Confirmation
        if scores.get("confirmation", 0) > 0.4:
            return ("confirmation", scores["confirmation"])
        
        # Applied
        if scores.get("applied", 0) > 0.3:
            return ("applied", scores["applied"])
        
        # Default: no_reply (if no match)
        return ("no_reply", 0.0)
    
    def extract_company_name(self, from_address: str, subject: str) -> Optional[str]:
        """Extract company name from email"""
        # Try to extract from email domain or sender name
        # Pattern: "Name <email@company.com>"
        match = re.search(r'([^<]+)<', from_address)
        if match:
            name = match.group(1).strip().strip('"').strip("'")
            if name and len(name) < 100:  # Reasonable name length
                return name
        
        # Extract from domain
        match = re.search(r'@([a-zA-Z0-9.-]+)\.', from_address)
        if match:
            domain = match.group(1)
            # Remove common email service providers
            if domain not in ["gmail", "yahoo", "outlook", "hotmail", "icloud", "mail"]:
                return domain.replace(".", " ").title()
        
        return None
    
    def classify_emails(self, emails: List[Dict]) -> List[Dict]:
        """Classify multiple emails and add status information (optimized for batch processing)"""
        classified = []
        for email_data in emails:
            try:
                status, confidence = self.classify_email(
                    email_data.get("subject", ""),
                    email_data.get("body", ""),
                    email_data.get("from", "")
                )
                
                company = self.extract_company_name(
                    email_data.get("from", ""),
                    email_data.get("subject", "")
                )
                
                classified.append({
                    **email_data,
                    "status": status,
                    "confidence": confidence,
                    "company": company or "Unknown"
                })
            except Exception:
                # If classification fails, add with default values
                classified.append({
                    **email_data,
                    "status": "no_reply",
                    "confidence": 0.0,
                    "company": "Unknown"
                })
        
        return classified

