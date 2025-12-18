"""Analytics and visualization generation"""

import json
from typing import Dict, List
from collections import defaultdict, Counter
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go

from src.config import ANALYTICS_JSON, ANALYTICS_CSV, SANKEY_HTML


class AnalyticsGenerator:
    """Generates analytics and visualizations from classified emails"""
    
    def __init__(self, emails: List[Dict]):
        self.emails = emails
        self.stats = self._calculate_stats()
    
    def _calculate_stats(self) -> Dict:
        """Calculate statistics from classified emails"""
        stats = {
            "total_emails": len(self.emails),
            "by_status": Counter(),
            "by_company": defaultdict(lambda: {"count": 0, "statuses": []}),
            "date_range": {"earliest": None, "latest": None},
            "applications": [],
        }
        
        for email_data in self.emails:
            status = email_data.get("status", "no_reply")
            company = email_data.get("company", "Unknown")
            date = email_data.get("date")
            
            stats["by_status"][status] += 1
            stats["by_company"][company]["count"] += 1
            stats["by_company"][company]["statuses"].append(status)
            
            if date:
                if not stats["date_range"]["earliest"] or date < stats["date_range"]["earliest"]:
                    stats["date_range"]["earliest"] = date
                if not stats["date_range"]["latest"] or date > stats["date_range"]["latest"]:
                    stats["date_range"]["latest"] = date
            
            stats["applications"].append({
                "company": company,
                "status": status,
                "date": date.isoformat() if date else None,
                "subject": email_data.get("subject", ""),
                "confidence": email_data.get("confidence", 0.0)
            })
        
        return stats
    
    def calculate_accuracy(self) -> float:
        """Calculate classification accuracy based on confidence scores"""
        if not self.emails:
            return 0.0
        
        total_confidence = sum(email.get("confidence", 0.0) for email in self.emails)
        average_confidence = total_confidence / len(self.emails)
        
        # Convert average confidence to percentage
        # Emails with confidence > 0.5 are considered "accurate"
        high_confidence_count = sum(
            1 for email in self.emails 
            if email.get("confidence", 0.0) > 0.5
        )
        
        accuracy_percentage = (high_confidence_count / len(self.emails)) * 100
        
        return round(accuracy_percentage, 2)
    
    def generate_summary(self) -> Dict:
        """Generate summary statistics"""
        # Calculate total applications (exclude no_reply from application count)
        application_statuses = [s for s in self.stats["by_status"].keys() if s != "no_reply"]
        total_applications = sum(
            count for status, count in self.stats["by_status"].items() 
            if status != "no_reply"
        )
        
        # Use applied + confirmation as initial applications
        applied_count = self.stats["by_status"].get("applied", 0)
        confirmation_count = self.stats["by_status"].get("confirmation", 0)
        # If we don't have explicit applied/confirmation, use total - no_reply
        if total_applications == 0:
            total_applications = self.stats["total_emails"]
        
        accuracy = self.calculate_accuracy()
        
        summary = {
            "total_applications": total_applications,
            "status_breakdown": dict(self.stats["by_status"]),
            "total_companies": len(self.stats["by_company"]),
            "date_range": {
                "earliest": self.stats["date_range"]["earliest"].isoformat() 
                    if self.stats["date_range"]["earliest"] else None,
                "latest": self.stats["date_range"]["latest"].isoformat() 
                    if self.stats["date_range"]["latest"] else None,
            },
            "rejected_count": self.stats["by_status"].get("rejected", 0),
            "offers_count": self.stats["by_status"].get("offer", 0),
            "accepted_count": self.stats["by_status"].get("accepted", 0),
            "interviews_count": sum(
                count for status, count in self.stats["by_status"].items() 
                if status.startswith("interview_")
            ),
            "withdrew_count": self.stats["by_status"].get("withdrew", 0),
            "no_reply_count": self.stats["by_status"].get("no_reply", 0),
            "applied_count": applied_count,
            "confirmation_count": confirmation_count,
            "accuracy_percentage": accuracy,
        }
        return summary
    
    def generate_sankey_diagram(self) -> go.Figure:
        """Generate Sankey diagram similar to the image"""
        # Count applications by source (applied vs recruiter)
        applied_count = self.stats["by_status"].get("applied", 0)
        recruiter_count = self.stats["by_status"].get("confirmation", 0)
        
        # Calculate total applications
        # If we have explicit applied/confirmation, use sum
        # Otherwise, calculate from all statuses except no_reply
        if applied_count > 0 or recruiter_count > 0:
            total_applications = applied_count + recruiter_count
        else:
            total_applications = sum(
                count for status, count in self.stats["by_status"].items() 
                if status not in ["no_reply", "applied", "confirmation"]
            )
        
        # If still 0, use total emails
        if total_applications == 0:
            total_applications = self.stats["total_emails"]
        
        # Build flow data
        labels = []
        source_indices = []
        target_indices = []
        values = []
        colors = []
        
        # Color scheme
        color_map = {
            "applied": "rgba(173, 216, 230, 0.8)",  # Light blue
            "recruiter": "rgba(173, 216, 230, 0.8)",
            "total": "rgba(173, 216, 230, 0.8)",
            "no_reply": "rgba(173, 216, 230, 0.6)",
            "rejected": "rgba(255, 165, 0, 0.8)",  # Orange/peach
            "interview": "rgba(255, 165, 0, 0.6)",
            "offer": "rgba(144, 238, 144, 0.8)",  # Light green
            "accepted": "rgba(144, 238, 144, 0.8)",
            "declined": "rgba(144, 238, 144, 0.6)",
            "withdrew": "rgba(255, 165, 0, 0.6)",
        }
        
        label_index = {}
        current_index = 0
        
        def get_or_add_label(label):
            nonlocal current_index
            if label not in label_index:
                label_index[label] = current_index
                labels.append(label)
                current_index += 1
            return label_index[label]
        
        # Applied sources
        if applied_count > 0:
            applied_idx = get_or_add_label("Applied")
            labels[applied_idx] = f"Applied ({applied_count})"
        
        if recruiter_count > 0:
            recruiter_idx = get_or_add_label("Recruiter")
            labels[recruiter_idx] = f"Recruiter ({recruiter_count})"
        
        # Total Applications
        total_idx = get_or_add_label("Total Applications")
        labels[total_idx] = f"Total Applications ({total_applications})"
        
        # Connect sources to total (only if we have them)
        if applied_count > 0:
            source_indices.append(applied_idx)
            target_indices.append(total_idx)
            values.append(applied_count)
            colors.append(color_map["applied"])
        
        if recruiter_count > 0:
            source_indices.append(recruiter_idx)
            target_indices.append(total_idx)
            values.append(recruiter_count)
            colors.append(color_map["recruiter"])
        
        # If no explicit sources, we need to adjust total
        if applied_count == 0 and recruiter_count == 0:
            # Set total to actual total
            labels[total_idx] = f"Total Applications ({total_applications})"
        
        # Outcomes from total applications
        no_reply_count = self.stats["by_status"].get("no_reply", 0)
        rejected_total = self.stats["by_status"].get("rejected", 0)
        
        if no_reply_count > 0:
            no_reply_idx = get_or_add_label("No Reply")
            labels[no_reply_idx] = f"No Reply ({no_reply_count})"
            source_indices.append(total_idx)
            target_indices.append(no_reply_idx)
            values.append(no_reply_count)
            colors.append(color_map["no_reply"])
        
        if rejected_total > 0:
            rejected_idx = get_or_add_label("Rejected")
            labels[rejected_idx] = f"Rejected ({rejected_total})"
            source_indices.append(total_idx)
            target_indices.append(rejected_idx)
            values.append(rejected_total)
            colors.append(color_map["rejected"])
        
        # Interview stages (build chain)
        interview_stages = []
        for i in range(1, 6):
            status = f"interview_{i}"
            count = self.stats["by_status"].get(status, 0)
            if count > 0:
                interview_stages.append((i, count))
        
        # Track the last interview stage index for connecting offers
        last_interview_idx = total_idx
        
        if interview_stages:
            # First interview connects from total
            stage_num, count = interview_stages[0]
            stage_label = f"First Interview"
            stage_idx = get_or_add_label(stage_label)
            labels[stage_idx] = f"{stage_label} ({count})"
            
            source_indices.append(total_idx)
            target_indices.append(stage_idx)
            values.append(count)
            colors.append(color_map["interview"])
            
            last_interview_idx = stage_idx
            
            # Subsequent interviews connect in sequence
            for stage_num, count in interview_stages[1:]:
                prev_stage_idx = last_interview_idx
                stage_label = f"Interview {stage_num}" if stage_num == 2 else f"Interview {stage_num}"
                stage_idx = get_or_add_label(stage_label)
                labels[stage_idx] = f"{stage_label} ({count})"
                
                source_indices.append(prev_stage_idx)
                target_indices.append(stage_idx)
                values.append(count)
                colors.append(color_map["interview"])
                
                last_interview_idx = stage_idx
        
        # Withdrew (can happen from any interview stage or directly)
        withdrew_count = self.stats["by_status"].get("withdrew", 0)
        if withdrew_count > 0:
            withdrew_idx = get_or_add_label("Withdrew Application")
            labels[withdrew_idx] = f"Withdrew Application ({withdrew_count})"
            # Connect from last interview stage if exists, otherwise from total
            source_indices.append(last_interview_idx if interview_stages else total_idx)
            target_indices.append(withdrew_idx)
            values.append(withdrew_count)
            colors.append(color_map["withdrew"])
        
        # Offer (connects from last interview stage or total)
        offer_count = self.stats["by_status"].get("offer", 0)
        if offer_count > 0:
            offer_idx = get_or_add_label("Offer")
            labels[offer_idx] = f"Offer ({offer_count})"
            source_indices.append(last_interview_idx if interview_stages else total_idx)
            target_indices.append(offer_idx)
            values.append(offer_count)
            colors.append(color_map["offer"])
            
            # From Offer: Accepted and Declined
            accepted_count = self.stats["by_status"].get("accepted", 0)
            declined_count = offer_count - accepted_count
            
            if accepted_count > 0:
                accepted_idx = get_or_add_label("Accepted")
                labels[accepted_idx] = f"Accepted ({accepted_count})"
                source_indices.append(offer_idx)
                target_indices.append(accepted_idx)
                values.append(accepted_count)
                colors.append(color_map["accepted"])
            
            if declined_count > 0:
                declined_idx = get_or_add_label("Declined")
                labels[declined_idx] = f"Declined ({declined_count})"
                source_indices.append(offer_idx)
                target_indices.append(declined_idx)
                values.append(declined_count)
                colors.append(color_map["declined"])
        
        # Create Sankey diagram
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=labels,
                color="lightblue"
            ),
            link=dict(
                source=source_indices,
                target=target_indices,
                value=values,
                color=colors
            )
        )])
        
        fig.update_layout(
            title_text="Job Application Flow - Sankey Diagram",
            font_size=12,
            height=800
        )
        
        return fig
    
    def save_analytics(self):
        """Save analytics to JSON and CSV files"""
        summary = self.generate_summary()
        summary["applications"] = self.stats["applications"]
        summary["company_details"] = {
            company: {
                "count": data["count"],
                "statuses": Counter(data["statuses"])
            }
            for company, data in self.stats["by_company"].items()
        }
        
        # Save JSON
        with open(ANALYTICS_JSON, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, default=str, ensure_ascii=False)
        
        # Save CSV
        df = pd.DataFrame(self.stats["applications"])
        df.to_csv(ANALYTICS_CSV, index=False, encoding='utf-8')
        
        # Save Sankey diagram
        fig = self.generate_sankey_diagram()
        fig.write_html(str(SANKEY_HTML))
        
        return summary

