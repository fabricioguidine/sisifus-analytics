"""Tests for email classifier logic"""

import pytest
from src.classifier import EmailClassifier


class TestEmailClassifier:
    """Test cases for EmailClassifier"""
    
    @pytest.fixture
    def classifier(self):
        """Create classifier instance"""
        return EmailClassifier()
    
    def test_classify_applied(self, classifier):
        """Test classification of application emails"""
        subject = "Application submitted"
        body = "Thank you for applying to our company"
        status, confidence = classifier.classify_email(subject, body)
        assert status == "applied"
        assert confidence > 0.3
    
    def test_classify_confirmation(self, classifier):
        """Test classification of confirmation emails"""
        subject = "Application Confirmation"
        body = "We have received your application for the position"
        status, confidence = classifier.classify_email(subject, body)
        assert status == "confirmation"
        assert confidence > 0.4
    
    def test_classify_interview_1(self, classifier):
        """Test classification of first interview emails"""
        subject = "First Interview Invitation"
        body = "We would like to invite you for a phone screen interview"
        status, confidence = classifier.classify_email(subject, body)
        assert status == "interview_1"
        assert confidence > 0.4
    
    def test_classify_interview_2(self, classifier):
        """Test classification of second interview emails"""
        subject = "Second Round Interview"
        body = "Congratulations, we would like to proceed with a technical interview"
        status, confidence = classifier.classify_email(subject, body)
        assert status == "interview_2"
        assert confidence > 0.4
    
    def test_classify_interview_3(self, classifier):
        """Test classification of third interview emails"""
        subject = "Final Interview"
        body = "We would like to invite you for an onsite interview"
        status, confidence = classifier.classify_email(subject, body)
        assert status == "interview_3"
        assert confidence > 0.4
    
    def test_classify_offer(self, classifier):
        """Test classification of job offer emails"""
        subject = "Job Offer"
        body = "We are pleased to offer you the position"
        status, confidence = classifier.classify_email(subject, body)
        assert status == "offer"
        assert confidence > 0.5
    
    def test_classify_accepted(self, classifier):
        """Test classification of accepted offer emails"""
        subject = "Offer Accepted"
        body = "I am excited to accept the offer and join your team"
        status, confidence = classifier.classify_email(subject, body)
        assert status == "accepted"
        assert confidence > 0.5
    
    def test_classify_rejected(self, classifier):
        """Test classification of rejection emails"""
        subject = "Application Status Update"
        body = "Unfortunately, we have decided not to move forward with your application"
        status, confidence = classifier.classify_email(subject, body)
        assert status == "rejected"
        assert confidence > 0.5
    
    def test_classify_rejected_variations(self, classifier):
        """Test various rejection email phrasings"""
        rejection_phrases = [
            "we will not be moving forward",
            "not selected for this position",
            "decided to pursue other candidates",
            "not the right fit at this time",
            "regret to inform you",
        ]
        
        for phrase in rejection_phrases:
            subject = "Application Update"
            body = f"Thank you for your interest. {phrase}."
            status, confidence = classifier.classify_email(subject, body)
            assert status == "rejected", f"Failed for phrase: {phrase}"
            assert confidence > 0.4
    
    def test_classify_withdrew(self, classifier):
        """Test classification of withdrawal emails"""
        subject = "Withdrawing Application"
        body = "I would like to withdraw my application for this position"
        status, confidence = classifier.classify_email(subject, body)
        assert status == "withdrew"
        assert confidence > 0.5
    
    def test_rejection_priority(self, classifier):
        """Test that rejection takes priority over other statuses"""
        subject = "Interview Update"
        body = "Thank you for the interview. Unfortunately, we have decided not to move forward"
        status, confidence = classifier.classify_email(subject, body)
        assert status == "rejected"
    
    def test_offer_priority_over_interview(self, classifier):
        """Test that offer takes priority over interview stages"""
        subject = "Next Steps"
        body = "We would like to offer you the position after your interviews"
        status, confidence = classifier.classify_email(subject, body)
        assert status == "offer"
    
    def test_extract_company_name_from_email(self, classifier):
        """Test company name extraction from email address"""
        from_addr = "John Doe <john@example-company.com>"
        company = classifier.extract_company_name(from_addr, "")
        assert company is not None
        assert "example-company" in company.lower() or "john doe" in company.lower()
    
    def test_extract_company_name_from_domain(self, classifier):
        """Test company name extraction from domain"""
        from_addr = "hr@techstartup.com"
        company = classifier.extract_company_name(from_addr, "")
        assert company is not None
        assert "techstartup" in company.lower()
    
    def test_classify_multiple_emails(self, classifier):
        """Test batch classification"""
        emails = [
            {"subject": "Application submitted", "body": "Thank you", "from": "test@company.com"},
            {"subject": "First Interview", "body": "Phone screen", "from": "hr@company.com"},
            {"subject": "Job Offer", "body": "We offer you", "from": "manager@company.com"},
        ]
        
        classified = classifier.classify_emails(emails)
        assert len(classified) == 3
        assert classified[0]["status"] == "applied"
        assert classified[1]["status"] == "interview_1"
        assert classified[2]["status"] == "offer"
        assert all("confidence" in email for email in classified)
        assert all("company" in email for email in classified)
    
    def test_no_reply_classification(self, classifier):
        """Test that unrelated emails get no_reply status"""
        subject = "Newsletter"
        body = "Check out our latest products"
        status, confidence = classifier.classify_email(subject, body)
        assert status == "no_reply"
        assert confidence == 0.0
    
    def test_confidence_scores(self, classifier):
        """Test that confidence scores are reasonable"""
        test_cases = [
            ("Application submitted", "Thank you for applying"),
            ("First Interview", "Phone screen invitation"),
            ("Job Offer", "We are pleased to offer"),
            ("Rejected", "Not moving forward"),
        ]
        
        for subject, body in test_cases:
            status, confidence = classifier.classify_email(subject, body)
            assert 0.0 <= confidence <= 1.0
            if status != "no_reply":
                assert confidence > 0.0


