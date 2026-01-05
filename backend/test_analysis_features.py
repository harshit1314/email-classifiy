"""
Test Priority Detection, Sentiment Analysis, and Entity Extraction
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.priority_service import PriorityDetector
from app.services.sentiment_service import SentimentAnalyzer
from app.services.entity_extraction_service import EntityExtractor


def test_all_features():
    print("=" * 70)
    print("🔬 Testing Email Analysis Features")
    print("=" * 70)
    
    # Initialize services
    print("\n🔧 Initializing services...")
    priority_detector = PriorityDetector()
    sentiment_analyzer = SentimentAnalyzer(use_transformers=False)  # Rule-based for speed
    entity_extractor = EntityExtractor()
    print("✅ All services initialized\n")
    
    # Test emails
    test_emails = [
        {
            "subject": "URGENT: Server Down - Production Issue",
            "body": """Hi Team,
            
Our main production server crashed at 3:45 PM. All customers are affected.
We need immediate assistance! Please call me ASAP at (555) 123-4567.

This is a P1 critical issue. We're losing $50,000 per hour.

Thanks,
John Smith
CEO, Acme Corp
john.smith@acme.com""",
            "sender": "john.smith@acme.com"
        },
        {
            "subject": "Thank you for the amazing support!",
            "body": """Dear Support Team,
            
I just wanted to say thank you for the excellent help yesterday. Sarah was incredibly 
helpful and resolved my issue quickly. I'm so impressed with your service!

Best regards,
Emily Johnson""",
            "sender": "emily.j@gmail.com"
        },
        {
            "subject": "Invoice #INV-2024-5678 - Payment Due",
            "body": """Please find attached invoice #INV-2024-5678 for $12,500.00.
            
Payment is due by January 15, 2025. You can wire transfer to our account or
pay online at https://payments.example.com/inv/5678

Contact billing@example.com or call 1-800-555-9876 for questions.

Thank you,
Accounting Department
Example Corp LLC""",
            "sender": "billing@example.com"
        },
        {
            "subject": "Complaint - Worst experience ever!!!",
            "body": """I am EXTREMELY frustrated with your company! I've been waiting 
for 3 weeks for my order #ORD-789456 and still nothing!

This is absolutely ridiculous. I demand a full refund of $299.99 immediately!
I will be filing a complaint with the Better Business Bureau.

My phone number is 555-987-6543. Call me TODAY or I'm posting this on social media!

Very disappointed customer,
Mike Brown""",
            "sender": "mike.brown@yahoo.com"
        },
        {
            "subject": "FYI - Weekly Newsletter",
            "body": """Hi everyone,

Here's your weekly digest of company news. No action needed.

- Team lunch on Friday
- Office closed on December 31st
- New parking policy starts next month

Have a great week!
HR Team""",
            "sender": "newsletter@company.com"
        }
    ]
    
    for i, email in enumerate(test_emails, 1):
        print(f"\n{'='*70}")
        print(f"📧 EMAIL {i}: {email['subject'][:50]}...")
        print(f"{'='*70}")
        
        # Priority Detection
        print("\n🔴 PRIORITY DETECTION:")
        priority = priority_detector.detect_priority(email["subject"], email["body"], email["sender"])
        icon = priority_detector.get_priority_icon(priority["priority"])
        print(f"   {icon} Level: {priority['priority'].upper()}")
        print(f"   Confidence: {priority['confidence']:.0%}")
        print(f"   Recommendation: {priority['recommendation']}")
        if priority['indicators']:
            print(f"   Indicators: {', '.join(priority['indicators'][:3])}")
        
        # Sentiment Analysis
        print("\n😊 SENTIMENT ANALYSIS:")
        sentiment = sentiment_analyzer.analyze_sentiment(email["subject"], email["body"])
        print(f"   {sentiment.get('icon', '?')} Sentiment: {sentiment['sentiment'].upper()}")
        print(f"   Confidence: {sentiment['confidence']:.0%}")
        print(f"   Summary: {sentiment.get('summary', '')[:80]}")
        emotions = sentiment.get('emotions', {})
        top_emotions = sorted(emotions.items(), key=lambda x: -x[1])[:2]
        if top_emotions and top_emotions[0][1] > 0:
            print(f"   Top Emotions: {', '.join([f'{e[0]}({e[1]:.0%})' for e in top_emotions if e[1] > 0])}")
        
        # Entity Extraction
        print("\n🔍 ENTITY EXTRACTION:")
        entities = entity_extractor.extract_entities(email["subject"], email["body"], email["sender"])
        print(f"   Total entities found: {entities['total_entities']}")
        
        if entities['emails']:
            print(f"   📧 Emails: {', '.join([e['value'] for e in entities['emails'][:3]])}")
        if entities['phones']:
            print(f"   📞 Phones: {', '.join([p['value'] for p in entities['phones'][:3]])}")
        if entities['money']:
            print(f"   💰 Money: {', '.join([m['original'] for m in entities['money'][:3]])}")
        if entities['dates']:
            print(f"   📅 Dates: {', '.join([d['original'] for d in entities['dates'][:3]])}")
        if entities['names']:
            print(f"   👤 Names: {', '.join([n['value'] for n in entities['names'][:3]])}")
        if entities['companies']:
            print(f"   🏢 Companies: {', '.join([c['value'] for c in entities['companies'][:3]])}")
        if entities['order_numbers']:
            print(f"   🔢 References: {', '.join([o['value'] for o in entities['order_numbers'][:3]])}")
        if entities['urls']:
            print(f"   🔗 URLs: {', '.join([u['domain'] for u in entities['urls'][:3]])}")
    
    print(f"\n{'='*70}")
    print("✅ All tests completed!")
    print(f"{'='*70}")


if __name__ == "__main__":
    test_all_features()
