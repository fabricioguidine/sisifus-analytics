"""Analytics and visualization generation"""

import json
from typing import Dict, List
from collections import defaultdict, Counter
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
from tqdm import tqdm

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
        
        print("Calculating statistics...")
        error_count = 0
        try:
            for email_data in tqdm(self.emails, desc="Analyzing emails", unit="email"):
                try:
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
                except Exception as e:
                    error_count += 1
                    if error_count <= 5:
                        print(f"\n[WARNING] Error processing email for stats: {e}")
                    continue
        except KeyboardInterrupt:
            print(f"\n[INFO] Statistics calculation interrupted by user")
        
        if error_count > 0:
            print(f"[WARNING] {error_count} emails had errors during statistics calculation")
        
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
        # Exclude non-job emails from application count
        excluded_statuses = {"no_reply", "not_job_related"}
        
        # Calculate total applications (exclude no_reply and not_job_related)
        total_applications = sum(
            count for status, count in self.stats["by_status"].items() 
            if status not in excluded_statuses
        )
        
        # Use applied + confirmation as initial applications
        applied_count = self.stats["by_status"].get("applied", 0)
        confirmation_count = self.stats["by_status"].get("confirmation", 0)
        
        # Calculate accuracy only for job-related emails
        job_related_emails = [
            email for email in self.emails 
            if email.get("status") not in excluded_statuses
        ]
        if job_related_emails:
            accuracy = self._calculate_accuracy_for_emails(job_related_emails)
        else:
            accuracy = 0.0
        
        summary = {
            "total_applications": total_applications,
            "status_breakdown": dict(self.stats["by_status"]),
            "total_companies": len([c for c, data in self.stats["by_company"].items() 
                                    if any(s not in excluded_statuses for s in data.get("statuses", []))]),
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
            "not_job_related_count": self.stats["by_status"].get("not_job_related", 0),
            "applied_count": applied_count,
            "confirmation_count": confirmation_count,
            "accuracy_percentage": accuracy,
        }
        return summary
    
    def _calculate_accuracy_for_emails(self, emails: List[Dict]) -> float:
        """Calculate accuracy for a specific set of emails"""
        if not emails:
            return 0.0
        
        high_confidence_count = sum(
            1 for email in emails 
            if email.get("confidence", 0.0) > 0.5
        )
        
        accuracy_percentage = (high_confidence_count / len(emails)) * 100
        return round(accuracy_percentage, 2)
    
    def _get_company_flow(self) -> Dict[str, Dict]:
        """Determine the flow for each company based on all their emails"""
        company_flows = {}
        
        for email_data in self.emails:
            company = email_data.get("company", "Unknown")
            status = email_data.get("status", "no_reply")
            
            if company not in company_flows:
                company_flows[company] = {
                    "highest_interview": 0,
                    "final_status": "no_reply",
                    "has_offer": False,
                    "has_accepted": False,
                    "has_rejected": False,
                    "has_withdrew": False,
                }
            
            flow = company_flows[company]
            
            # Track highest interview stage
            if status.startswith("interview_"):
                try:
                    stage_num = int(status.split("_")[1])
                    flow["highest_interview"] = max(flow["highest_interview"], stage_num)
                except:
                    pass
            
            # Track final status (priority order: accepted > offer > withdrew > rejected > interview > applied)
            if status == "accepted":
                flow["has_accepted"] = True
                flow["final_status"] = "accepted"
            elif status == "offer" and flow["final_status"] != "accepted":
                flow["has_offer"] = True
                flow["final_status"] = "offer"
            elif status == "withdrew" and flow["final_status"] not in ["accepted", "offer"]:
                flow["has_withdrew"] = True
                flow["final_status"] = "withdrew"
            elif status == "rejected" and flow["final_status"] not in ["accepted", "offer", "withdrew"]:
                flow["has_rejected"] = True
                flow["final_status"] = "rejected"
            elif status.startswith("interview_") and flow["final_status"] == "no_reply":
                flow["final_status"] = f"interview_{flow['highest_interview']}"
        
        return company_flows
    
    def generate_sankey_diagram(self) -> go.Figure:
        """Generate Sankey diagram with accurate company flow tracking"""
        # Get company flows to determine actual outcomes
        company_flows = self._get_company_flow()
        
        # Count applications by source
        applied_count = self.stats["by_status"].get("applied", 0)
        recruiter_count = self.stats["by_status"].get("confirmation", 0)
        
        excluded_statuses = {"no_reply", "not_job_related"}
        
        if applied_count > 0 or recruiter_count > 0:
            total_applications = applied_count + recruiter_count
        else:
            total_applications = sum(
                count for status, count in self.stats["by_status"].items() 
                if status not in excluded_statuses
            )
        
        # Count companies by their actual flow outcome
        flow_counts = {
            "rejected_from_interview": {},  # interview stage -> count (rejected after this stage)
            "rejected_direct": 0,  # rejected without interview
            "withdrew_from_interview": {},  # interview stage -> count
            "withdrew_direct": 0,
            "ghosted_from_interview": {},  # interview stage -> count (ghosted after this stage)
            "ghosted_direct": 0,  # ghosted without interview
            "offer": 0,
            "accepted": 0,
            "declined_offer": 0,
        }
        
        for company, flow in company_flows.items():
            if company == "Unknown":
                continue  # Skip Unknown companies
            highest = flow["highest_interview"]
            final = flow["final_status"]
            
            if flow["has_accepted"]:
                flow_counts["accepted"] += 1
            elif flow["has_offer"]:
                if flow["has_withdrew"] or not flow["has_accepted"]:
                    flow_counts["declined_offer"] += 1
                else:
                    flow_counts["offer"] += 1
            elif flow["has_withdrew"]:
                if highest > 0:
                    if highest not in flow_counts["withdrew_from_interview"]:
                        flow_counts["withdrew_from_interview"][highest] = 0
                    flow_counts["withdrew_from_interview"][highest] += 1
                else:
                    flow_counts["withdrew_direct"] += 1
            elif flow["has_rejected"]:
                if highest > 0:
                    # Rejected after reaching interview stage
                    if highest not in flow_counts["rejected_from_interview"]:
                        flow_counts["rejected_from_interview"][highest] = 0
                    flow_counts["rejected_from_interview"][highest] += 1
                else:
                    flow_counts["rejected_direct"] += 1
            elif highest > 0:
                # Reached interview but no clear outcome - ghosted after interview
                if highest not in flow_counts["ghosted_from_interview"]:
                    flow_counts["ghosted_from_interview"][highest] = 0
                flow_counts["ghosted_from_interview"][highest] += 1
            else:
                # No interview, no clear outcome - ghosted directly
                flow_counts["ghosted_direct"] += 1
        
        # Build Sankey diagram
        labels = []
        source_indices = []
        target_indices = []
        values = []
        colors = []
        
        color_map = {
            "applied": "rgba(173, 216, 230, 0.8)",
            "recruiter": "rgba(173, 216, 230, 0.8)",
            "total": "rgba(173, 216, 230, 0.8)",
            "no_reply": "rgba(173, 216, 230, 0.6)",
            "rejected": "rgba(255, 165, 0, 0.8)",
            "interview": "rgba(255, 165, 0, 0.6)",
            "offer": "rgba(144, 238, 144, 0.8)",
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
        
        # Connect sources to total
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
        
        # Create single Rejected node (will be populated later if needed)
        total_rejected = flow_counts["rejected_direct"] + sum(flow_counts["rejected_from_interview"].values())
        rejected_idx = None
        if total_rejected > 0:
            rejected_idx = get_or_add_label("Rejected")
            labels[rejected_idx] = f"Rejected ({total_rejected})"
            if flow_counts["rejected_direct"] > 0:
                # Direct rejected (no interview)
                source_indices.append(total_idx)
                target_indices.append(rejected_idx)
                values.append(flow_counts["rejected_direct"])
                colors.append(color_map["rejected"])
        
        # Create single Withdrew node (will be populated later if needed)
        total_withdrew = flow_counts["withdrew_direct"] + sum(flow_counts["withdrew_from_interview"].values())
        withdrew_idx = None
        if total_withdrew > 0:
            withdrew_idx = get_or_add_label("Withdrew")
            labels[withdrew_idx] = f"Withdrew ({total_withdrew})"
            if flow_counts["withdrew_direct"] > 0:
                # Direct withdrew (no interview)
                source_indices.append(total_idx)
                target_indices.append(withdrew_idx)
                values.append(flow_counts["withdrew_direct"])
                colors.append(color_map["withdrew"])
        
        # Create single Ghosted node (will be populated later if needed)
        total_ghosted = flow_counts["ghosted_direct"] + sum(flow_counts["ghosted_from_interview"].values())
        ghosted_idx = None
        if total_ghosted > 0:
            ghosted_idx = get_or_add_label("Ghosted")
            labels[ghosted_idx] = f"Ghosted ({total_ghosted})"
            if flow_counts["ghosted_direct"] > 0:
                # Direct ghosted (no interview)
                source_indices.append(total_idx)
                target_indices.append(ghosted_idx)
                values.append(flow_counts["ghosted_direct"])
                colors.append(color_map["no_reply"])
        
        # Interview stages with flows - only connect consecutive stages
        # If a higher stage exists, assume all previous stages were reached
        interview_stage_indices = {}
        existing_stages = sorted(set(list(flow_counts["rejected_from_interview"].keys()) +
                                    list(flow_counts["withdrew_from_interview"].keys()) +
                                    list(flow_counts["ghosted_from_interview"].keys())))
        
        # Fill in missing intermediate stages
        # If Interview 5 exists but Interview 4 doesn't, add Interview 4 with count 0
        sorted_stages = []
        if existing_stages:
            max_stage = max(existing_stages)
            for i in range(1, max_stage + 1):
                if i in existing_stages or i < max_stage:
                    sorted_stages.append(i)
        
        last_stage_idx = total_idx
        last_stage_num = 0  # Track the actual stage number
        
        for stage_num in sorted_stages:
            # Create interview stage node
            stage_label = f"Interview {stage_num}" if stage_num > 1 else "First Interview"
            stage_idx = get_or_add_label(stage_label)
            
            # Count companies that reached this stage
            rejected_after = flow_counts["rejected_from_interview"].get(stage_num, 0)
            withdrew_after = flow_counts["withdrew_from_interview"].get(stage_num, 0)
            ghosted_after = flow_counts["ghosted_from_interview"].get(stage_num, 0)
            total_at_stage = rejected_after + withdrew_after + ghosted_after
            
            # If this is a missing intermediate stage (inferred from higher stages),
            # use the count from the next stage that has data
            if total_at_stage == 0 and stage_num < max(existing_stages) if existing_stages else 0:
                # This is an inferred stage - estimate count from next stage
                # Use the minimum of stages after this one as estimate
                next_stages = [s for s in existing_stages if s > stage_num]
                if next_stages:
                    # Use count from next existing stage as estimate for missing stage
                    next_stage = min(next_stages)
                    estimated_rejected = flow_counts["rejected_from_interview"].get(next_stage, 0)
                    estimated_withdrew = flow_counts["withdrew_from_interview"].get(next_stage, 0)
                    estimated_ghosted = flow_counts["ghosted_from_interview"].get(next_stage, 0)
                    total_at_stage = estimated_rejected + estimated_withdrew + estimated_ghosted
            
            labels[stage_idx] = f"{stage_label} ({total_at_stage})"
            interview_stage_indices[stage_num] = stage_idx
            
            # Only connect from previous consecutive stage (now all stages are consecutive)
            if last_stage_num > 0 and stage_num == last_stage_num + 1:
                # Consecutive stage - connect from previous
                source_indices.append(last_stage_idx)
                target_indices.append(stage_idx)
                values.append(total_at_stage)
                colors.append(color_map["interview"])
            elif last_stage_num == 0:
                # First interview stage - connect from total
                source_indices.append(total_idx)
                target_indices.append(stage_idx)
                values.append(total_at_stage)
                colors.append(color_map["interview"])
            else:
                # This shouldn't happen now, but handle it gracefully
                source_indices.append(total_idx)
                target_indices.append(stage_idx)
                values.append(total_at_stage)
                colors.append(color_map["interview"])
            
            # Flow to rejected (companies rejected after this interview)
            if rejected_after > 0:
                # Use the single Rejected node (created earlier)
                if rejected_idx is None:
                    rejected_idx = get_or_add_label("Rejected")
                    labels[rejected_idx] = f"Rejected ({total_rejected})"
                source_indices.append(stage_idx)
                target_indices.append(rejected_idx)
                values.append(rejected_after)
                colors.append(color_map["rejected"])
            
            # Flow to withdrew (companies that withdrew after this interview)
            if withdrew_after > 0:
                # Use the single Withdrew node (created earlier)
                if withdrew_idx is None:
                    withdrew_idx = get_or_add_label("Withdrew")
                    labels[withdrew_idx] = f"Withdrew ({total_withdrew})"
                source_indices.append(stage_idx)
                target_indices.append(withdrew_idx)
                values.append(withdrew_after)
                colors.append(color_map["withdrew"])
            
            # Ghosted after this interview stage
            ghosted_after = flow_counts["ghosted_from_interview"].get(stage_num, 0)
            if ghosted_after > 0:
                # Use the single Ghosted node (created earlier)
                if ghosted_idx is None:
                    ghosted_idx = get_or_add_label("Ghosted")
                    labels[ghosted_idx] = f"Ghosted ({total_ghosted})"
                source_indices.append(stage_idx)
                target_indices.append(ghosted_idx)
                values.append(ghosted_after)
                colors.append(color_map["no_reply"])
            
            # Update tracking for next iteration
            last_stage_idx = stage_idx
            last_stage_num = stage_num
        
        # Offer flow (from last interview stage)
        if flow_counts["offer"] > 0 or flow_counts["accepted"] > 0 or flow_counts["declined_offer"] > 0:
            total_offers = flow_counts["offer"] + flow_counts["accepted"] + flow_counts["declined_offer"]
            offer_idx = get_or_add_label("Offer")
            labels[offer_idx] = f"Offer ({total_offers})"
            source_indices.append(last_stage_idx if interview_stage_indices else total_idx)
            target_indices.append(offer_idx)
            values.append(total_offers)
            colors.append(color_map["offer"])
            
            if flow_counts["accepted"] > 0:
                accepted_idx = get_or_add_label("Accepted")
                labels[accepted_idx] = f"Accepted ({flow_counts['accepted']})"
                source_indices.append(offer_idx)
                target_indices.append(accepted_idx)
                values.append(flow_counts["accepted"])
                colors.append(color_map["accepted"])
            
            if flow_counts["declined_offer"] > 0:
                declined_idx = get_or_add_label("Declined Offer")
                labels[declined_idx] = f"Declined ({flow_counts['declined_offer']})"
                source_indices.append(offer_idx)
                target_indices.append(declined_idx)
                values.append(flow_counts["declined_offer"])
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
        print("Generating summary statistics...")
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
        print(f"Saving analytics JSON to {ANALYTICS_JSON.name}...")
        with open(ANALYTICS_JSON, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, default=str, ensure_ascii=False)
        
        # Save CSV
        print(f"Saving analytics CSV to {ANALYTICS_CSV.name}...")
        df = pd.DataFrame(self.stats["applications"])
        df.to_csv(ANALYTICS_CSV, index=False, encoding='utf-8')
        
        # Save Sankey diagram
        print(f"Generating Sankey diagram...")
        fig = self.generate_sankey_diagram()
        print(f"Saving Sankey diagram to {SANKEY_HTML.name}...")
        fig.write_html(str(SANKEY_HTML))
        
        return summary

