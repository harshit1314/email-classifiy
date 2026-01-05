"""
Entity Extraction Service - Enhanced
Extracts: Names, Emails, Phone Numbers, Dates, Money, Companies, Order Numbers
"""
import re
from typing import Dict, List, Any
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class EntityExtractor:
    """
    Enhanced entity extraction from emails
    """
    
    PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone": r'(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)(?:\d{3}[-.\s]?)(?:\d{4})(?:\s*(?:ext|x)\s*\d+)?',
        "money": r'\$[\d,]+(?:\.\d{2})?|\b\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars?|USD)\b',
        "order_number": r'(?i)(?:order|invoice|ref|ticket|case|po|confirmation|tracking)[\s#:]+([A-Z0-9]+-?[A-Z0-9]+)',
        "url": r'https?://[^\s<>"{}|\\^`\[\]]+',
        "date": r'(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4})|(?:\d{4}[/-]\d{1,2}[/-]\d{1,2})|(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s*\d{4})',
        "time": r'\b(?:1[0-2]|0?[1-9]):[0-5][0-9]\s*(?:am|pm|AM|PM)|(?:2[0-3]|[01]?[0-9]):[0-5][0-9]\b',
        "percentage": r'\b\d+(?:\.\d+)?%',
    }
    
    COMPANY_SUFFIXES = ["Inc", "LLC", "Ltd", "Corp", "Corporation", "Company", "Co", "Solutions", "Services", "Group", "Technologies"]

    def __init__(self):
        self.compiled_patterns = {name: re.compile(pattern, re.IGNORECASE) for name, pattern in self.PATTERNS.items()}
        logger.info("Enhanced Entity Extraction Service initialized")

    def extract_entities(self, subject: str, body: str, sender_email: str = "") -> Dict:
        """Extract all entities from email"""
        text = f"{subject}\n{body}"
        
        entities = {
            "emails": self._extract_emails(text, sender_email),
            "phones": self._extract_phones(text),
            "money": self._extract_money(text),
            "dates": self._extract_dates(text),
            "times": self._extract_times(text),
            "urls": self._extract_urls(text),
            "order_numbers": self._extract_order_numbers(text),
            "names": self._extract_names(text),
            "companies": self._extract_companies(text),
            "percentages": self._extract_percentages(text),
        }
        
        entities["summary"] = self._generate_summary(entities)
        entities["total_entities"] = sum(len(v) for v in entities.values() if isinstance(v, list))
        
        return entities

    def _extract_emails(self, text: str, exclude: str = "") -> List[Dict]:
        """Extract email addresses"""
        matches = self.compiled_patterns["email"].findall(text)
        seen = set()
        emails = []
        for email in matches:
            if email.lower() not in seen and email.lower() != exclude.lower():
                seen.add(email.lower())
                emails.append({"value": email, "type": self._classify_email(email)})
        return emails

    def _classify_email(self, email: str) -> str:
        e = email.lower()
        if any(x in e for x in ["support", "help"]): return "support"
        if any(x in e for x in ["sales", "business"]): return "sales"
        if any(x in e for x in ["noreply", "no-reply"]): return "automated"
        return "personal"

    def _extract_phones(self, text: str) -> List[Dict]:
        """Extract phone numbers"""
        matches = self.compiled_patterns["phone"].findall(text) if self.compiled_patterns["phone"].search(text) else []
        # Use finditer for complex patterns
        phones = []
        seen = set()
        for match in re.finditer(self.PATTERNS["phone"], text, re.IGNORECASE):
            phone = match.group().strip()
            cleaned = re.sub(r'[^\d+]', '', phone)
            if len(cleaned) >= 10 and cleaned not in seen:
                seen.add(cleaned)
                phones.append({"value": phone, "cleaned": cleaned})
        return phones

    def _extract_money(self, text: str) -> List[Dict]:
        """Extract monetary amounts"""
        matches = self.compiled_patterns["money"].findall(text)
        amounts = []
        for match in matches:
            cleaned = re.sub(r'[^\d.]', '', match)
            try:
                value = float(cleaned)
                amounts.append({"original": match, "value": value, "currency": "USD"})
            except ValueError:
                continue
        return amounts

    def _extract_dates(self, text: str) -> List[Dict]:
        """Extract dates"""
        matches = self.compiled_patterns["date"].findall(text)
        dates = []
        seen = set()
        for match in matches:
            if match not in seen:
                seen.add(match)
                dates.append({"original": match, "parsed": match})
        
        # Relative dates
        today = datetime.now()
        relatives = [
            (r'\b(today)\b', 0), (r'\b(tomorrow)\b', 1), (r'\b(yesterday)\b', -1),
            (r'\b(next week)\b', 7), (r'\b(this week)\b', 0), (r'\b(end of week)\b', 4-today.weekday())
        ]
        for pattern, days in relatives:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                target = today + timedelta(days=days)
                dates.append({"original": match.group(1), "parsed": target.strftime("%Y-%m-%d"), "relative": match.group(1)})
        return dates

    def _extract_times(self, text: str) -> List[str]:
        return list(set(self.compiled_patterns["time"].findall(text)))

    def _extract_urls(self, text: str) -> List[Dict]:
        matches = self.compiled_patterns["url"].findall(text)
        return [{"value": url, "domain": re.search(r'https?://(?:www\.)?([^/]+)', url).group(1) if re.search(r'https?://(?:www\.)?([^/]+)', url) else url} for url in matches]

    def _extract_order_numbers(self, text: str) -> List[Dict]:
        matches = self.compiled_patterns["order_number"].findall(text)
        seen = set()
        orders = []
        for match in matches:
            # Filter out false positives - must contain numbers and be reasonable length
            if match.upper() not in seen and len(match) >= 5 and any(c.isdigit() for c in match):
                seen.add(match.upper())
                orders.append({"value": match.upper(), "type": "reference"})
        return orders

    def _extract_names(self, text: str) -> List[Dict]:
        """Extract person names"""
        names = []
        
        # After greetings
        for match in re.findall(r'(?:dear|hi|hello|hey)[,\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', text, re.IGNORECASE):
            if len(match) > 2:
                names.append({"value": match.strip(), "context": "greeting"})
        
        # Titles
        for match in re.findall(r'(?:Mr|Mrs|Ms|Dr)\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', text):
            names.append({"value": match.strip(), "context": "titled"})
        
        # Signatures
        for match in re.findall(r'(?:thanks|regards|sincerely|best)[,\s]*\n+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', text, re.IGNORECASE):
            if len(match) > 2:
                names.append({"value": match.strip(), "context": "signature"})
        
        # Dedupe
        seen = set()
        unique = []
        for n in names:
            if n["value"].lower() not in seen:
                seen.add(n["value"].lower())
                unique.append(n)
        return unique

    def _extract_companies(self, text: str) -> List[Dict]:
        """Extract company names"""
        companies = []
        
        # Look for patterns like "Company Name Inc" or "Company Name LLC"
        for suffix in self.COMPANY_SUFFIXES:
            # Match: Word(s) starting with capital + suffix
            pattern = rf'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+{suffix}\.?\b'
            for match in re.findall(pattern, text):
                company_name = f"{match} {suffix}".strip()
                if len(company_name) > 3 and len(company_name) < 50:
                    companies.append({"value": company_name, "confidence": "high"})
        
        # Dedupe
        seen = set()
        unique = []
        for c in companies:
            key = c["value"].lower()
            if key not in seen:
                seen.add(key)
                unique.append(c)
        return unique

    def _extract_percentages(self, text: str) -> List[Dict]:
        matches = self.compiled_patterns["percentage"].findall(text)
        return [{"value": m, "numeric": float(m.replace('%', ''))} for m in matches]

    def _generate_summary(self, entities: Dict) -> Dict:
        """Generate summary"""
        summary = {
            "has_contact_info": bool(entities["emails"] or entities["phones"]),
            "has_financial_data": bool(entities["money"]),
            "has_dates": bool(entities["dates"]),
            "has_references": bool(entities["order_numbers"]),
            "key_entities": []
        }
        
        if entities["money"]:
            total = sum(m["value"] for m in entities["money"])
            summary["key_entities"].append(f"${total:,.2f} mentioned")
        if entities["dates"]:
            summary["key_entities"].append(f"{len(entities['dates'])} date(s)")
        if entities["order_numbers"]:
            summary["key_entities"].append(f"Ref: {entities['order_numbers'][0]['value']}")
        if entities["names"]:
            summary["key_entities"].append(f"Name: {entities['names'][0]['value']}")
        
        return summary


# Legacy compatibility
class EntityExtractionService(EntityExtractor):
    """Legacy wrapper - use EntityExtractor instead"""
    
    def extract_entities(self, text: str) -> Dict[str, List[Any]]:
        """Legacy method signature"""
        return super().extract_entities("", text, "")


def extract_entities(subject: str, body: str, sender: str = "") -> Dict:
    """Extract entities from email"""
    extractor = EntityExtractor()
    return extractor.extract_entities(subject, body, sender)
