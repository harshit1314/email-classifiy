import re
import os

file_path = r'd:\ai-email-classifier\backend\app\ml\improved_classifier.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Define the new training data method content
new_method = """    def get_expanded_training_data(self) -> List[Tuple[str, str, str]]:
        \"\"\"Get comprehensive training dataset focused on company departments\"\"\"
        # Import training data from external module if available
        try:
            from app.ml.training_data import ENTERPRISE_TRAINING_DATA
            # Convert enterprise categories to our categories
            category_map = {
                'sales': 'sales',
                'hr': 'hr',
                'finance': 'finance',
                'it_support': 'support',
                'marketing': 'marketing',
                'customer_service': 'support'
            }
            
            # Add enterprise data with mapped categories
            enterprise_examples = [
                (subj, body, category_map[cat.lower()])
                for subj, body, cat in ENTERPRISE_TRAINING_DATA
                if cat.lower() in category_map
            ]
        except:
            enterprise_examples = []
        
        # Core training examples for departments
        core_examples = [
            # HR
            ("Payroll Inquiry", "I have a question about my last paycheck. The overtime hours seem incorrect.", "hr"),
            ("Benefits Enrollment", "Open enrollment for company benefits ends this Friday. Please complete your selection.", "hr"),
            ("Onboarding Documents", "Welcome to the team! Please sign and return the attached onboarding documents.", "hr"),
            ("Leave Request", "I would like to request time off from July 10th to July 15th for a family vacation.", "hr"),
            ("Employee Handbook", "Please review the updated employee handbook and sign the acknowledgment form.", "hr"),
            ("Hiring Update", "We've scheduled interviews for the Senior Engineer position starting next Tuesday.", "hr"),
            ("Resignation Notice", "This email serves as my formal resignation from my position, effective in two weeks.", "hr"),
            ("Training Completion", "Thank you for completing the mandatory compliance training. Your certificate is attached.", "hr"),
            ("Performance Review", "It's time for your mid-year performance review. Let's schedule a 30-minute call.", "hr"),
            ("Job Posting", "We've just posted a new opening for a Project Manager. Referrals are welcome!", "hr"),
            ("Hiring Process", "What is the current status of the hiring process for the marketing lead role?", "hr"),
            ("Employee Relations", "I need to discuss a sensitive matter regarding a teammate. Are you available for a call?", "hr"),
            ("New Policy Acknowledgment", "I have read and agree to the new workplace conduct policy.", "hr"),
            ("Recruitment Strategy", "Our recruitment strategy for next year needs to focus on diversity and inclusion.", "hr"),
            ("Candidate Feedback", "The feedback for the candidate we interviewed yesterday is mostly positive.", "hr"),

            # FINANCE
            ("Budget Approval", "The Q3 budget for the engineering department has been approved. See attached for details.", "finance"),
            ("Expense Reimbursement", "Your expense report for the business trip has been processed and approved for payment.", "finance"),
            ("Quarterly Audit", "The external auditors will be onsite next week. Please have all financial docs ready.", "finance"),
            ("Tax Documentation", "Your 1099 form for the last fiscal year is now available for download.", "finance"),
            ("Invoice Processing", "Please process the attached invoice from Vendor X for the software licenses.", "finance"),
            ("Revenue Forecast", "Attached is the revenue forecast for the next six months based on current trends.", "finance"),
            ("P&L Statement", "The monthly Profit and Loss statement is ready for review by the executive team.", "finance"),
            ("Fiscal Year End", "As we approach the end of the fiscal year, please ensure all outstanding invoices are submitted.", "finance"),
            ("Audit Findings", "The preliminary audit findings are attached. We need to address these items by Friday.", "finance"),
            ("Treasury Management", "Moving funds to the operational account to cover upcoming payroll and vendor payments.", "finance"),
            ("Billing Discrepancy", "There is a discrepancy in the latest billing statement for our cloud services.", "finance"),
            ("Bank Statement Request", "Could you provide the bank statements for the last three months for the audit?", "finance"),
            ("Capital Expenditure", "Requesting approval for the capital expenditure needed for the new server hardware.", "finance"),
            ("Financial Reporting", "The monthly financial report is due by the 5th. Please ensure all data is accurate.", "finance"),
            ("Tax Filing Deadline", "Reminder that the corporate tax filing deadline is approaching next month.", "finance"),

            # MARKETING
            ("Campaign Launch", "Our new summer marketing campaign goes live tomorrow across all social platforms.", "marketing"),
            ("Social Media Strategy", "Attached is the proposed social media strategy for the next quarter. Please provide feedback.", "marketing"),
            ("Brand Guidelines", "Please ensure all new assets follow the updated brand guidelines for color and typography.", "marketing"),
            ("SEO Report", "Our organic search rankings have improved by 15% this month. See the full report.", "marketing"),
            ("Content Calendar", "The content calendar for next month is now available on the shared drive.", "marketing"),
            ("Lead Generation", "We've seen a spike in leads from the recent webinar. Sales team, please follow up.", "marketing"),
            ("Ad Spend Optimization", "Adjusting the Google Ads spend to focus on higher-converting keywords.", "marketing"),
            ("Market Research", "The results of the latest customer satisfaction survey are in. Review the summary attached.", "marketing"),
            ("Partner Promotion", "Co-marketing opportunity with Partner Y. See the attached proposal for details.", "marketing"),
            ("Webinar Preparation", "Everything is set for the 'Future of Tech' webinar. Don't forget to register!", "marketing"),
            ("Email Newsletter", "The draft for the monthly email newsletter is ready for your review.", "marketing"),
            ("Press Release", "Our latest press release has been picked up by several major tech publications.", "marketing"),
            ("Brand Awareness", "We need to increase our brand awareness in the European market next year.", "marketing"),
            ("Customer Personas", "Updating our customer personas based on the latest demographic data.", "marketing"),
            ("Marketing Automation", "Evaluating new marketing automation tools to streamline our lead nurturing process.", "marketing"),

            # SALES
            ("New Lead: Company Z", "We just received a high-quality lead from Company Z. Assigning this to the West Coast team.", "sales"),
            ("Pipeline Update", "The sales pipeline is looking strong for Q4. Several large deals are in the final stages.", "sales"),
            ("Deal Closed: Project X", "Congratulations! We've officially closed the deal with Project X. Kickoff meeting soon.", "sales"),
            ("Sales Forecast", "Based on current progress, we are on track to beat our sales target for the month.", "sales"),
            ("Prospecting Call", "Scheduled a discovery call with a potential client in the fintech space for Wednesday.", "sales"),
            ("Sales Commission", "Commissions for the last quarter have been calculated and will be paid with next payroll.", "sales"),
            ("Customer Acquisition Cost", "Analysis shows our CAC has decreased by 10% through more targeted outreach.", "sales"),
            ("Quota Achievement", "Celebrating our top performers who exceeded their sales quota this month!", "sales"),
            ("Partnership Outreach", "Reaching out to potential partners in the retail sector to expand our reach.", "sales"),
            ("Demo Request", "A new prospect has requested a demo of our platform. Scheduling for Thursday morning.", "sales"),
            ("Inbound Lead Inquiry", "A new inbound lead from the website is interested in our enterprise plan.", "sales"),
            ("Sales Outreach Sequence", "Reviewing the sales outreach sequence for the new product line.", "sales"),
            ("Key Account Management", "Strategy meeting for managing our top 5 key accounts for the coming year.", "sales"),
            ("Sales Enablement Tools", "Training session for the new sales enablement tools scheduled for next week.", "sales"),
            ("Closing Strategy", "Discussing the closing strategy for the large deal with Company Y.", "sales"),

            # SUPPORT
            ("Help with Login Issue", "I can't log into my account. Getting 'invalid password' error even after reset.", "support"),
            ("Feature Request: Export Function", "Would be great to have a CSV export option for reports. Is this planned?", "support"),
            ("Bug Report: Page Not Loading", "The dashboard page keeps showing a blank screen in Chrome. Works in Firefox.", "support"),
            ("How to Cancel Subscription", "I'd like to cancel my subscription. Can you guide me through the process?", "support"),
            ("Product Question: Compatibility", "Does your product work with Windows 11? Can't find this in documentation.", "support"),
            ("Account Upgrade Request", "I'd like to upgrade from Basic to Premium plan. What's the process?", "support"),
            ("Missing Order Items", "My order arrived but item #3 was missing from the package. Need replacement.", "support"),
            ("Technical Support Needed", "Getting error code 500 when trying to upload files. Attached screenshot.", "support"),
            ("Billing Question", "Why was I charged twice this month? Need explanation of charges.", "support"),
            ("Password Reset Not Working", "The password reset email never arrives. Checked spam folder already.", "support"),
            ("Ticket Opened", "Support ticket #789 opened: Unable to log into account. Our team is investigating the issue.", "support"),
            ("Request Received", "Your request has been received. A support agent will respond within 24 hours. Ticket #1234", "support"),
            ("Issue Resolved", "Issue resolved: Your billing problem has been fixed. Refund of $49.99 processed to your card.", "support"),
            ("Troubleshooting Guide", "Troubleshooting guide: Common solutions for the error you reported. Try these steps first.", "support"),
            ("Knowledge Base", "Knowledge base article: How to reset your password and recover your account access.", "support"),
        ]
        
        # Combine all examples
        all_examples = enterprise_examples + core_examples
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Total training examples: {len(all_examples)} (core: {len(core_examples)}, enterprise: {len(enterprise_examples)})")
        
        return all_examples"""

# Pattern to find the get_expanded_training_data method
pattern = re.compile(r'    def get_expanded_training_data\(self\) -> List\[Tuple\[str, str, str\]\]:.*?        return all_examples', re.DOTALL)

if pattern.search(content):
    new_content = pattern.sub(new_method, content)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Successfully updated get_expanded_training_data")
else:
    # Try more robust pattern if the first one fails
    alt_pattern = re.compile(r'    def get_expanded_training_data\(self\).*?(?=    def train_model)', re.DOTALL)
    if alt_pattern.search(content):
        new_content = alt_pattern.sub(new_method + "\\n\\n", content)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Successfully updated get_expanded_training_data (alt pattern)")
    else:
        print("Could not find the method to replace")
