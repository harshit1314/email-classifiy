"""
Enterprise Email Classifier - Department Routing for Large Organizations
Fine-tunable model for classifying emails to: Sales, HR, Finance, IT, Legal, Marketing, Support, Operations, Executive
"""
import os
import torch
import numpy as np
import json
import pickle
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification,
    pipeline,
    Trainer,
    TrainingArguments,
    DataCollatorWithPadding
)
from datasets import Dataset
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class EnterpriseEmailClassifier:
    """
    Enterprise-grade email classifier for routing to company departments.
    Supports fine-tuning on company-specific data for higher accuracy.
    """
    
    # Department categories for enterprise use
    DEPARTMENTS = [
        "sales",           # Sales inquiries, quotes, deals, pricing
        "hr",              # Human resources, recruitment, benefits, policies
        "finance",         # Billing, invoices, payments, accounting
        "it_support",      # Technical support, IT issues, system access
        "legal",           # Contracts, compliance, legal matters
        "marketing",       # Campaigns, promotions, brand, PR
        "customer_service", # Customer complaints, feedback, general inquiries
        "operations",      # Logistics, supply chain, facilities
        "executive",       # C-level communications, board matters
        "general"          # Miscellaneous, unclassified
    ]
    
    # Detailed descriptions for zero-shot classification
    DEPARTMENT_DESCRIPTIONS = {
        "sales": "sales inquiry, pricing request, quote request, product demo, purchase order, deal negotiation, sales proposal, business development, revenue opportunity, client acquisition, sales pitch, discount request, bulk order",
        
        "hr": "human resources, job application, resume, recruitment, hiring, employee benefits, payroll question, vacation request, sick leave, performance review, training, onboarding, workplace policy, HR inquiry, compensation, termination, resignation",
        
        "finance": "invoice, payment, billing, accounting, expense report, reimbursement, budget, financial statement, tax, audit, accounts payable, accounts receivable, purchase order approval, financial inquiry, credit, refund request",
        
        "it_support": "technical support, IT help, password reset, system access, software issue, hardware problem, network issue, computer problem, login issue, email problem, VPN access, security incident, data recovery, IT request, technology support",
        
        "legal": "legal matter, contract review, NDA, non-disclosure agreement, compliance, regulatory, lawsuit, legal notice, intellectual property, trademark, copyright, terms and conditions, privacy policy, legal inquiry, litigation",
        
        "marketing": "marketing campaign, advertising, brand, public relations, PR, social media, content marketing, email marketing, event promotion, press release, market research, branding, promotional material, marketing request",
        
        "customer_service": "customer complaint, customer feedback, product issue, service problem, dissatisfied customer, refund request, exchange request, product return, customer inquiry, support ticket, help request, customer question",
        
        "operations": "logistics, shipping, delivery, supply chain, warehouse, inventory, facilities, office management, vendor management, procurement, supplier, manufacturing, production, operational issue",
        
        "executive": "CEO, CFO, CTO, board meeting, executive summary, strategic decision, investor relations, board of directors, C-level, executive communication, leadership, company strategy, merger, acquisition",
        
        "general": "general inquiry, miscellaneous, newsletter, notification, update, announcement, information request, other"
    }
    
    # Keywords for boosting classification confidence
    DEPARTMENT_KEYWORDS = {
        "sales": [
            "quote", "pricing", "demo", "purchase", "buy", "deal", "discount", 
            "proposal", "sales", "order", "subscription", "upgrade", "renew",
            "interested in", "looking to buy", "price list", "cost", "roi",
            "trial", "pilot", "poc", "proof of concept", "budget approved"
        ],
        "hr": [
            "job", "resume", "cv", "application", "interview", "hiring", "recruit",
            "salary", "benefits", "vacation", "leave", "pto", "sick", "payroll",
            "performance", "review", "training", "onboarding", "policy", "handbook",
            "termination", "resignation", "retire", "promotion", "raise"
        ],
        "finance": [
            "invoice", "payment", "bill", "receipt", "expense", "reimburse",
            "budget", "accounting", "tax", "audit", "payable", "receivable",
            "purchase order", "po number", "credit", "debit", "refund", "wire transfer",
            "bank", "financial", "quarterly", "fiscal", "revenue", "profit"
        ],
        "it_support": [
            "password", "reset", "login", "access", "system", "computer", "laptop",
            "software", "hardware", "install", "update", "network", "wifi", "vpn",
            "email setup", "outlook", "teams", "printer", "monitor", "mouse",
            "slow", "crash", "error", "bug", "not working", "broken", "help desk"
        ],
        "legal": [
            "contract", "agreement", "nda", "legal", "lawyer", "attorney", "lawsuit",
            "compliance", "regulation", "gdpr", "privacy", "terms", "conditions",
            "intellectual property", "trademark", "copyright", "patent", "liability",
            "indemnification", "arbitration", "dispute", "court", "litigation"
        ],
        "marketing": [
            "campaign", "marketing", "advertising", "ad", "brand", "logo", "pr",
            "press release", "social media", "twitter", "linkedin", "facebook",
            "content", "blog", "newsletter", "webinar", "event", "conference",
            "analytics", "seo", "ppc", "lead generation", "conversion"
        ],
        "customer_service": [
            "complaint", "unhappy", "dissatisfied", "frustrated", "problem with",
            "issue with", "not satisfied", "return", "exchange", "refund",
            "broken", "defective", "damaged", "wrong", "missing", "late delivery",
            "poor service", "bad experience", "feedback", "suggestion", "help"
        ],
        "operations": [
            "shipping", "delivery", "tracking", "warehouse", "inventory", "stock",
            "supply chain", "supplier", "vendor", "procurement", "logistics",
            "facility", "office", "maintenance", "equipment", "fleet", "manufacturing",
            "production", "quality control", "shipment", "freight", "customs"
        ],
        "executive": [
            "ceo", "cfo", "cto", "coo", "cmo", "board", "director", "chairman",
            "investor", "shareholder", "strategic", "merger", "acquisition", "ipo",
            "quarterly report", "annual report", "earnings", "executive", "leadership",
            "confidential", "board meeting", "executive summary", "priority"
        ]
    }
    
    def __init__(self, model_name: str = "typeform/distilbert-base-uncased-mnli", use_cuda: bool = False):
        """
        Initialize Enterprise Email Classifier
        
        Args:
            model_name: Base model for zero-shot classification
            use_cuda: Whether to use GPU acceleration
        """
        self.model_name = model_name
        self.device = "cuda" if use_cuda and torch.cuda.is_available() else "cpu"
        self.classifier = None
        self.tokenizer = None
        self.fine_tuned_model = None
        self.is_fine_tuned = False
        
        # Paths for saving fine-tuned models
        self.model_dir = os.path.join(os.path.dirname(__file__), "enterprise_model")
        self.training_data_path = os.path.join(self.model_dir, "training_data.json")
        
        logger.info(f"Initializing Enterprise Email Classifier on {self.device}")
        self._load_model()
    
    def _load_model(self):
        """Load the classification model"""
        try:
            # Check if we have a fine-tuned model
            fine_tuned_path = os.path.join(self.model_dir, "fine_tuned")
            if os.path.exists(fine_tuned_path):
                logger.info(f"Loading fine-tuned model from {fine_tuned_path}")
                self.tokenizer = AutoTokenizer.from_pretrained(fine_tuned_path)
                self.fine_tuned_model = AutoModelForSequenceClassification.from_pretrained(fine_tuned_path)
                self.fine_tuned_model.to(self.device)
                self.is_fine_tuned = True
                logger.info("✅ Fine-tuned enterprise model loaded")
            else:
                # Use zero-shot classification
                logger.info("Loading zero-shot classification model")
                self.classifier = pipeline(
                    "zero-shot-classification",
                    model=self.model_name,
                    device=0 if self.device == "cuda" else -1
                )
                logger.info("✅ Zero-shot classifier loaded")
                
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def _extract_keywords(self, text: str) -> Dict[str, List[str]]:
        """Extract matching keywords for each department"""
        text_lower = text.lower()
        found = {}
        
        for dept, keywords in self.DEPARTMENT_KEYWORDS.items():
            matches = [kw for kw in keywords if kw.lower() in text_lower]
            if matches:
                found[dept] = matches
                
        return found
    
    def _calculate_keyword_boost(self, found_keywords: Dict[str, List[str]]) -> Dict[str, float]:
        """Calculate confidence boost based on keywords"""
        boosts = {}
        total_keywords = sum(len(v) for v in found_keywords.values())
        
        for dept in self.DEPARTMENTS:
            count = len(found_keywords.get(dept, []))
            if count > 0:
                # Boost proportional to keyword matches
                boosts[dept] = min(count * 0.12, 0.4)  # Up to 40% boost
            elif total_keywords > 0:
                boosts[dept] = -0.05  # Small penalty if other depts have keywords
            else:
                boosts[dept] = 0.0
                
        return boosts
    
    def classify(self, subject: str, body: str, sender: str = "") -> Dict:
        """
        Classify email to appropriate department
        
        Args:
            subject: Email subject line
            body: Email body content
            sender: Sender email address (optional)
            
        Returns:
            Classification result with department, confidence, and probabilities
        """
        # Combine text
        text = f"Subject: {subject}\n\n{body}"[:2000]  # Limit length
        
        if not text.strip():
            return self._empty_result("Empty email content")
        
        # Extract keywords
        found_keywords = self._extract_keywords(text)
        boosts = self._calculate_keyword_boost(found_keywords)
        
        try:
            if self.is_fine_tuned and self.fine_tuned_model:
                return self._classify_fine_tuned(text, found_keywords, boosts)
            else:
                return self._classify_zero_shot(text, found_keywords, boosts)
                
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return self._empty_result(f"Classification error: {str(e)}")
    
    def _classify_zero_shot(self, text: str, found_keywords: Dict, boosts: Dict) -> Dict:
        """Classify using zero-shot model"""
        # Create labels with descriptions for better accuracy
        labels = list(self.DEPARTMENTS)
        
        result = self.classifier(
            text,
            candidate_labels=labels,
            hypothesis_template="This email should be routed to the {} department."
        )
        
        # Build probabilities with boosts
        probabilities = {}
        for label, score in zip(result['labels'], result['scores']):
            boost = boosts.get(label, 0)
            probabilities[label] = max(min(score + boost, 1.0), 0.0)
        
        # Normalize
        total = sum(probabilities.values())
        if total > 0:
            probabilities = {k: v/total for k, v in probabilities.items()}
        
        # Get top department
        department = max(probabilities, key=probabilities.get)
        confidence = probabilities[department]
        
        # Generate explanation
        keywords_found = found_keywords.get(department, [])
        explanation = self._generate_explanation(department, confidence, keywords_found)
        
        return {
            "category": department,
            "department": department,
            "confidence": confidence,
            "probabilities": {k: v * 100 for k, v in probabilities.items()},
            "explanation": explanation,
            "keywords_detected": found_keywords,
            "model_type": "zero-shot"
        }
    
    def _classify_fine_tuned(self, text: str, found_keywords: Dict, boosts: Dict) -> Dict:
        """Classify using fine-tuned model"""
        inputs = self.tokenizer(
            text,
            truncation=True,
            max_length=512,
            return_tensors="pt"
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.fine_tuned_model(**inputs)
            scores = torch.softmax(outputs.logits, dim=1)[0]
        
        # Build probabilities with boosts
        probabilities = {}
        for i, dept in enumerate(self.DEPARTMENTS):
            score = scores[i].item()
            boost = boosts.get(dept, 0)
            probabilities[dept] = max(min(score + boost, 1.0), 0.0)
        
        # Normalize
        total = sum(probabilities.values())
        if total > 0:
            probabilities = {k: v/total for k, v in probabilities.items()}
        
        department = max(probabilities, key=probabilities.get)
        confidence = probabilities[department]
        
        keywords_found = found_keywords.get(department, [])
        explanation = self._generate_explanation(department, confidence, keywords_found)
        
        return {
            "category": department,
            "department": department,
            "confidence": confidence,
            "probabilities": {k: v * 100 for k, v in probabilities.items()},
            "explanation": explanation,
            "keywords_detected": found_keywords,
            "model_type": "fine-tuned"
        }
    
    def _generate_explanation(self, department: str, confidence: float, keywords: List[str]) -> str:
        """Generate human-readable explanation"""
        dept_names = {
            "sales": "Sales Department",
            "hr": "Human Resources",
            "finance": "Finance Department",
            "it_support": "IT Support",
            "legal": "Legal Department",
            "marketing": "Marketing Department",
            "customer_service": "Customer Service",
            "operations": "Operations",
            "executive": "Executive Office",
            "general": "General Inbox"
        }
        
        dept_name = dept_names.get(department, department.title())
        
        if keywords:
            kw_str = ", ".join(keywords[:3])
            return f"Routed to {dept_name} ({confidence:.0%} confidence). Key indicators: {kw_str}"
        else:
            return f"Routed to {dept_name} ({confidence:.0%} confidence) based on content analysis"
    
    def _empty_result(self, reason: str) -> Dict:
        """Return empty/error result"""
        return {
            "category": "general",
            "department": "general",
            "confidence": 0.0,
            "probabilities": {d: 0.0 for d in self.DEPARTMENTS},
            "explanation": reason,
            "keywords_detected": {},
            "model_type": "none"
        }
    
    # ==================== Fine-Tuning Methods ====================
    
    def add_training_example(self, subject: str, body: str, department: str, sender: str = "") -> bool:
        """
        Add a training example for fine-tuning
        
        Args:
            subject: Email subject
            body: Email body
            department: Correct department (must be in DEPARTMENTS)
            sender: Sender email (optional)
            
        Returns:
            True if added successfully
        """
        if department not in self.DEPARTMENTS:
            logger.error(f"Invalid department: {department}. Must be one of {self.DEPARTMENTS}")
            return False
        
        # Load existing training data
        training_data = self._load_training_data()
        
        # Add new example
        training_data.append({
            "subject": subject,
            "body": body,
            "department": department,
            "sender": sender,
            "timestamp": datetime.now().isoformat()
        })
        
        # Save
        self._save_training_data(training_data)
        logger.info(f"Added training example for {department}. Total examples: {len(training_data)}")
        
        return True
    
    def add_training_examples_bulk(self, examples: List[Dict]) -> int:
        """
        Add multiple training examples at once
        
        Args:
            examples: List of dicts with keys: subject, body, department, sender (optional)
            
        Returns:
            Number of examples added successfully
        """
        training_data = self._load_training_data()
        added = 0
        
        for ex in examples:
            dept = ex.get("department", "").lower()
            if dept in self.DEPARTMENTS:
                training_data.append({
                    "subject": ex.get("subject", ""),
                    "body": ex.get("body", ""),
                    "department": dept,
                    "sender": ex.get("sender", ""),
                    "timestamp": datetime.now().isoformat()
                })
                added += 1
        
        self._save_training_data(training_data)
        logger.info(f"Added {added} training examples. Total: {len(training_data)}")
        
        return added
    
    def get_training_stats(self) -> Dict:
        """Get statistics about training data"""
        training_data = self._load_training_data()
        
        # Count by department
        counts = {d: 0 for d in self.DEPARTMENTS}
        for ex in training_data:
            dept = ex.get("department", "general")
            if dept in counts:
                counts[dept] += 1
        
        return {
            "total_examples": len(training_data),
            "by_department": counts,
            "is_fine_tuned": self.is_fine_tuned,
            "min_examples_to_fine_tune": 50,
            "ready_to_fine_tune": len(training_data) >= 50
        }
    
    def fine_tune(self, epochs: int = 3, batch_size: int = 8, learning_rate: float = 2e-5) -> Dict:
        """
        Fine-tune the model on collected training data
        
        Args:
            epochs: Number of training epochs
            batch_size: Training batch size
            learning_rate: Learning rate
            
        Returns:
            Training results
        """
        training_data = self._load_training_data()
        
        if len(training_data) < 50:
            return {
                "success": False,
                "error": f"Need at least 50 training examples. Currently have: {len(training_data)}"
            }
        
        logger.info(f"Starting fine-tuning with {len(training_data)} examples")
        
        try:
            # Prepare dataset
            texts = [f"Subject: {ex['subject']}\n\n{ex['body']}" for ex in training_data]
            labels = [self.DEPARTMENTS.index(ex['department']) for ex in training_data]
            
            # Load base model
            base_model = "distilbert-base-uncased"
            tokenizer = AutoTokenizer.from_pretrained(base_model)
            model = AutoModelForSequenceClassification.from_pretrained(
                base_model,
                num_labels=len(self.DEPARTMENTS)
            )
            
            # Tokenize
            def tokenize(examples):
                return tokenizer(examples["text"], truncation=True, max_length=512, padding=True)
            
            dataset = Dataset.from_dict({"text": texts, "label": labels})
            dataset = dataset.map(tokenize, batched=True)
            
            # Split train/eval
            split = dataset.train_test_split(test_size=0.1)
            
            # Training arguments
            output_dir = os.path.join(self.model_dir, "fine_tuned")
            os.makedirs(output_dir, exist_ok=True)
            
            training_args = TrainingArguments(
                output_dir=output_dir,
                num_train_epochs=epochs,
                per_device_train_batch_size=batch_size,
                per_device_eval_batch_size=batch_size,
                learning_rate=learning_rate,
                weight_decay=0.01,
                logging_steps=10,
                eval_strategy="epoch",
                save_strategy="epoch",
                load_best_model_at_end=True,
                push_to_hub=False
            )
            
            # Data collator
            data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
            
            # Trainer
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=split["train"],
                eval_dataset=split["test"],
                tokenizer=tokenizer,
                data_collator=data_collator
            )
            
            # Train
            trainer.train()
            
            # Save
            trainer.save_model(output_dir)
            tokenizer.save_pretrained(output_dir)
            
            # Reload fine-tuned model
            self._load_model()
            
            logger.info("✅ Fine-tuning complete!")
            
            return {
                "success": True,
                "examples_used": len(training_data),
                "epochs": epochs,
                "model_saved_to": output_dir
            }
            
        except Exception as e:
            logger.error(f"Fine-tuning failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _load_training_data(self) -> List[Dict]:
        """Load training data from file"""
        if os.path.exists(self.training_data_path):
            with open(self.training_data_path, 'r') as f:
                return json.load(f)
        return []
    
    def _save_training_data(self, data: List[Dict]):
        """Save training data to file"""
        os.makedirs(self.model_dir, exist_ok=True)
        with open(self.training_data_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.classifier is not None or self.fine_tuned_model is not None


# Convenience function
def create_enterprise_classifier(use_cuda: bool = False) -> EnterpriseEmailClassifier:
    """Create an enterprise email classifier instance"""
    return EnterpriseEmailClassifier(use_cuda=use_cuda)
