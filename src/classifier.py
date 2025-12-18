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
            r"your.*application",  # Generic application reference
            r"alert.*application",  # Application alerts
            r"candidate-se",  # Portuguese: apply now
            r"candidate.*se",  # Portuguese: apply
            r"aplicar",  # Portuguese: apply
            r"novas.*vagas",  # Portuguese: new jobs
            r"job.*opportunity",  # Job opportunities
            r".*opportunity",  # Opportunities (engineer, qa, etc.)
            r"vagas.*em",  # Portuguese: jobs in
            r"job.*alert",  # Job alerts
            r"new.*position",  # New positions
            r"open.*position",  # Open positions
            r"we.*are.*hiring",  # Hiring announcements
            r"looking.*for.*",  # Looking for candidates
        ],
        "confirmation": [
            r"confirmation.*application",
            r"application.*confirm",
            r"we.*have.*received.*application",
            r"application.*successfully.*received",
            r"confirm.*receipt.*application",
            r"application.*status.*update",  # Status updates
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
            r"first.*round.*interview",  # More explicit
            r"take.*home.*assessment",  # Take-home assignments
            r"assessment",  # Assessment/test
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
            # Company rejecting you - look for company/employer language
            r"we.*regret.*inform",
            r"we.*regret.*to.*inform",
            r"unfortunately.*not.*selected",
            r"unfortunately.*decided.*not.*to.*proceed",
            r"we.*decided.*not.*to.*proceed",
            r"we.*decided.*not.*proceed",
            r"we.*will.*not.*be.*moving.*forward",
            r"we.*will.*not.*move.*forward",
            r"we.*not.*move.*forward",
            r"we.*decided.*pursue.*other",
            r"decided.*not.*move.*forward",  # Sometimes without "we"
            r"other.*candidates",
            r"better.*fit.*another",
            r"not.*right.*fit",
            r"not.*fit.*at.*this.*time",
            r"we.*not.*advancing",
            # Generic rejection phrases (company perspective)
            r"not.*selected.*position",
            r"not.*selected.*candidate",
            r"not.*proceed.*with.*your.*application",
            r"not.*moving.*forward.*with.*application",
        ],
        "withdrew": [
            # You withdrawing/declining - look for user perspective language
            r"withdraw.*application",
            r"application.*withdrawn",
            r"no.*longer.*interested",
            r"decided.*to.*withdraw",
            r"withdrawing.*application",
            r"i.*withdraw",
            r"i.*no.*longer",
            r"declined.*interview",
            r"declined.*offer",
            r"will.*not.*be.*moving.*forward",  # Sometimes user says this
            r"not.*moving.*forward",  # Ambiguous - but often user-initiated
            r"decline.*opportunity",
            r"pass.*on.*opportunity",
            r"not.*pursue",
            r"decided.*not.*pursue",
        ],
    }
    
    def __init__(self):
        # Compile regex patterns for performance
        self.compiled_patterns = {}
        for status, patterns in self.STATUS_KEYWORDS.items():
            self.compiled_patterns[status] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
        
        # Job-related keywords to filter out non-job emails
        self.job_keywords = [
            r"job", r"application", r"interview", r"recruiter", r"hiring",
            r"position", r"candidate", r"opportunity", r"apply", r"career",
            r"resume", r"cv", r"employment", r"vacancy", r"role",
            r"application.*submitted", r"thank.*for.*your.*application",
            r"offer", r"rejection", r"withdraw.*application",
            r"linkedin", r"indeed", r"glassdoor", r"monster", r"ziprecruiter",
            r"ats", r"applicant.*tracking", r"job.*board",
            r"vaga", r"vagas",  # Portuguese: job/jobs
            r"emprego",  # Portuguese: employment
            r"trabalho",  # Portuguese: work
            r"candidate-se",  # Portuguese: apply now
            r"aplicar",  # Portuguese: apply
            r"engineer.*opportunity",  # Job opportunity patterns
            r".*engineer.*position",  # Engineering positions
            r"qa.*opportunity",  # QA positions
            r"automation.*qa",  # QA automation
        ]
        self.job_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.job_keywords]
    
    def is_job_related(self, subject: str, body: str, from_address: str = "") -> bool:
        """Check if email is related to job applications - improved filtering"""
        text = f"{subject} {body[:2000]} {from_address}".lower()
        
        # Exclude common non-job email patterns (strong exclusion signals)
        exclusion_patterns = [
            r"newsletter", r"unsubscribe", r"subscription", r"promo", r"promotion",
            r"black.*friday", r"cyber.*monday", r"sale", r"discount", r"coupon",
            r"receipt", r"invoice", r"payment.*received", r"order.*confirmation",
            r"flight.*confirmation", r"hotel.*booking", r"airbnb.*reservation",
            r"shipping.*confirmation", r"package.*delivered", r"tracking.*number",
            r"password.*reset", r"verify.*email.*address", r"account.*security",
            r"instagram.*follow", r"facebook.*friend", r"twitter.*notification",
        ]
        exclusion_regex = [re.compile(p, re.IGNORECASE) for p in exclusion_patterns]
        
        # If it matches exclusion patterns heavily AND has no job keywords, exclude it
        exclusion_matches = sum(1 for pattern in exclusion_regex if pattern.search(text))
        if exclusion_matches >= 2:
            # Check if there are job keywords despite exclusion patterns
            job_keyword_check = sum(1 for pattern in self.job_patterns if pattern.search(text))
            if job_keyword_check == 0:  # No job keywords at all
                return False
        
        # Check if any job keyword matches
        matches = sum(1 for pattern in self.job_patterns if pattern.search(text))
        
        # Job-related company domains/names
        job_companies = ["linkedin", "indeed", "glassdoor", "monster", "ziprecruiter", 
                         "flexjobs", "recruiter", "hiring", "careers", "talent",
                         "workday", "greenhouse", "lever", "smartrecruiters"]
        company_match = any(jc in from_address.lower() for jc in job_companies)
        
        # Job-related if: at least 1 keyword match OR job company domain
        # But exclude if strong exclusion signals (handled above)
        return (matches >= 1) or company_match
    
    def classify_email(self, subject: str, body: str, from_address: str = "") -> Tuple[str, float]:
        """
        Classify email into a status category.
        
        Returns:
            Tuple of (status, confidence_score)
            confidence_score is between 0.0 and 1.0
            Returns ("not_job_related", 0.0) if email is not job-related
        """
        # First check if email is job-related
        if not self.is_job_related(subject, body, from_address):
            return ("not_job_related", 0.0)
        
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
        
        # Applied - lower threshold to catch job board notifications and opportunities
        if scores.get("applied", 0) > 0.1:  # Lower threshold for more flexibility
            return ("applied", max(scores["applied"], 0.3))  # Minimum confidence of 0.3
        
        # Default: no_reply (if no match, but email is job-related)
        # This means email is job-related but doesn't fit any specific category
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

