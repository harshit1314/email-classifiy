"""
Test script for frontend-integrated analysis features.
Tests: Priority, Sentiment, Entity Extraction, Full Analysis, Smart Reply
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# Test email samples
TEST_EMAILS = [
    {
        "name": "Urgent IT Issue",
        "subject": "URGENT: Server Down - Production Environment",
        "body": """Hi IT Team,

This is CRITICAL! Our production server went down at 3:00 PM today and we are losing $5,000 per hour.
Customer orders are failing and we need immediate help. This is affecting Order #ORD-2024-78901.

Please escalate this ASAP!

Contact me at emergency@company.com or call 555-123-4567.

John Smith
Operations Manager""",
        "sender": "john.smith@company.com"
    },
    {
        "name": "Happy Customer Feedback",
        "subject": "Thank you for excellent service!",
        "body": """Dear Customer Service Team,

I just wanted to say THANK YOU for the amazing support I received yesterday. 
Sarah was incredibly helpful and resolved my issue within 10 minutes.

This is the best customer experience I've ever had! I will definitely recommend 
your company to my friends and colleagues.

Keep up the great work!

Best regards,
Emily Johnson""",
        "sender": "emily.johnson@gmail.com"
    },
    {
        "name": "Sales Inquiry",
        "subject": "Pricing inquiry for enterprise plan",
        "body": """Hello Sales Team,

I'm interested in your enterprise plan for our company (Acme Corporation).
We have approximately 500 employees and need pricing for the annual subscription.

Could you please send me a quote by December 15, 2024?

Our budget is around $50,000 per year.

Thanks,
Michael Brown
Procurement Manager
michael.brown@acmecorp.com
Phone: (555) 987-6543""",
        "sender": "michael.brown@acmecorp.com"
    }
]


def test_full_analysis():
    """Test the full analysis endpoint"""
    print("\n" + "="*60)
    print("TESTING FULL ANALYSIS ENDPOINT")
    print("="*60)
    
    for email in TEST_EMAILS:
        print(f"\n📧 Testing: {email['name']}")
        print("-" * 40)
        
        try:
            response = requests.post(f"{BASE_URL}/api/analyze/full", json={
                "subject": email["subject"],
                "body": email["body"],
                "sender": email["sender"]
            })
            
            if response.status_code == 200:
                result = response.json()
                
                # Classification
                print(f"  📁 Department: {result['classification']['department']}")
                print(f"     Confidence: {result['classification']['confidence']*100:.1f}%")
                
                # Priority
                print(f"  ⚡ Priority: {result['priority']['level'].upper()}")
                print(f"     Confidence: {result['priority']['confidence']*100:.1f}%")
                if result['priority'].get('indicators'):
                    print(f"     Indicators: {', '.join(result['priority']['indicators'][:3])}")
                
                # Sentiment
                print(f"  😊 Sentiment: {result['sentiment']['sentiment'].upper()}")
                print(f"     Summary: {result['sentiment'].get('summary', 'N/A')}")
                if result['sentiment'].get('emotions'):
                    emotions = [k for k, v in result['sentiment']['emotions'].items() if v]
                    if emotions:
                        print(f"     Emotions: {', '.join(emotions)}")
                
                # Entities
                print(f"  🔍 Entities: {result['entities']['total_entities']} found")
                for key, vals in result['entities'].items():
                    if key not in ['total_entities', 'summary'] and vals:
                        print(f"     {key}: {vals}")
                
                print("  ✅ SUCCESS")
            else:
                print(f"  ❌ Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")


def test_smart_reply():
    """Test the smart reply generation endpoint"""
    print("\n" + "="*60)
    print("TESTING SMART REPLY ENDPOINT")
    print("="*60)
    
    for email in TEST_EMAILS:
        print(f"\n📧 Testing: {email['name']}")
        print("-" * 40)
        
        try:
            response = requests.post(f"{BASE_URL}/api/replies/generate", json={
                "subject": email["subject"],
                "body": email["body"],
                "sender": email["sender"]
            })
            
            if response.status_code == 200:
                result = response.json()
                
                # Analysis summary
                if result.get('analysis'):
                    print(f"  📊 Analysis Used:")
                    print(f"     Department: {result['analysis']['department']}")
                    print(f"     Priority: {result['analysis']['priority']}")
                    print(f"     Sentiment: {result['analysis']['sentiment']}")
                    print(f"     Entities: {result['analysis']['entities_found']}")
                
                # Reply
                print(f"\n  📝 Generated Reply:")
                print(f"     Subject: {result['subject']}")
                print(f"     Body Preview: {result['body'][:150]}...")
                
                print("\n  ✅ SUCCESS")
            else:
                print(f"  ❌ Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")


def main():
    print("="*60)
    print("    FRONTEND INTEGRATION TEST SUITE")
    print("    Testing Analysis Features & Smart Reply")
    print("="*60)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"\n✅ Server is running at {BASE_URL}")
    except:
        print(f"\n⚠️  Server may not be running at {BASE_URL}")
        print("   Start the backend with: uvicorn app.main:app --reload")
    
    # Run tests
    test_full_analysis()
    test_smart_reply()
    
    print("\n" + "="*60)
    print("    TEST SUITE COMPLETE")
    print("="*60)
    print("\n📋 Summary:")
    print("   - Full Analysis: Tests priority, sentiment, entity extraction")
    print("   - Smart Reply: Tests context-aware reply generation")
    print("\n🖥️  Frontend Features Added:")
    print("   - EmailDetailModal: AI Analysis section with Analyze button")
    print("   - EmailDetailModal: Smart Reply section with Generate button")
    print("   - EmailsPage: Enhanced Smart Reply dialog with analysis badges")


if __name__ == "__main__":
    main()
