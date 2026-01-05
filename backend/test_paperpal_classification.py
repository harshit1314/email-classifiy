#!/usr/bin/env python3
"""
Test script to verify Paperpal email classification after fixes
"""

import requests
import json

def test_paperpal_email():
    """Test the Paperpal email that was previously misclassified"""
    
    # The actual email content from your screenshot
    email_data = {
        "subject": "We're delighted to present Paperpal",
        "body": """We're delighted to present Paperpal, the editing tool academics and researchers prefer.

Perfecting academic writing takes more than knowing what to say. It's about presenting your ideas with precise language. Paperpal goes beyond basic grammar checking to help you write like experts in your field.

Why academic experts choose Paperpal:
• Subject-area expertise: Get contextual help from a tool that understands academic language
• Perfect every detail: From tone to readability to structure, Paperpal helps you refine your writing
• Manuscript ready: Prepare submission-ready writing that meets publication standards

Experience the difference with Paperpal's advanced editing capabilities.

Start writing better today
www.paperpal.com

Team Paperpal

This email was sent to harsh@example.com
Unsubscribe from emails like this""",
        "sender": "team@paperpal.com"
    }
    
    url = "http://127.0.0.1:8000/api/process/classify"
    
    try:
        print("Testing Paperpal email classification...")
        print(f"Subject: {email_data['subject']}")
        print(f"From: {email_data['from_email']}")
        print("-" * 60)
        
        response = requests.post(url, json=email_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Classification Result:")
            print(f"Category: {result.get('decision', 'Unknown')}")
            print(f"Confidence: {result.get('confidence', 0):.1%}")
            print(f"Department: {result.get('department', 'Unknown')}")
            print(f"Urgency: {result.get('urgency', 'Unknown')}")
            
            # Show detailed probabilities
            if 'probabilities' in result:
                print("\n📊 Category Probabilities:")
                probs = result['probabilities']
                sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)
                for category, prob in sorted_probs:
                    print(f"  {category}: {prob:.1%}")
            
            # Check if it's now correctly classified
            category = result.get('decision', '').lower()
            if 'sales' in category or 'promotion' in category:
                print("\n✅ SUCCESS: Email is now correctly classified as promotional!")
                return True
            elif category == 'spam':
                print("\n❌ STILL WRONG: Email is still being classified as spam")
                return False
            else:
                print(f"\n⚠️  UNCERTAIN: Email classified as '{category}' - check if this is appropriate")
                return False
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API server. Make sure it's running on port 8000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_other_examples():
    """Test other email types to ensure they still work"""
    
    test_cases = [
        {
            "name": "Obvious Spam",
            "data": {
                "subject": "YOU WON $1,000,000! CLAIM NOW!",
                "body": "Congratulations! You have won the lottery. Click here immediately to claim your prize before it expires!",
                "sender": "noreply@scam.com"
            },
            "expected": "spam"
        },
        {
            "name": "Support Request", 
            "data": {
                "subject": "Password reset request",
                "body": "Please help me reset my password. I'm unable to access my account.",
                "sender": "user@company.com"
            },
            "expected": "support"
        },
        {
            "name": "Work Email",
            "data": {
                "subject": "Meeting tomorrow at 10am",
                "body": "Please confirm your attendance for the quarterly review meeting scheduled for tomorrow at 10am in Conference Room A.",
                "sender": "manager@company.com"
            },
            "expected": "important"
        }
    ]
    
    url = "http://127.0.0.1:8000/api/process/classify"
    
    for test_case in test_cases:
        print(f"\n🧪 Testing: {test_case['name']}")
        print(f"Subject: {test_case['data']['subject']}")
        
        try:
            response = requests.post(url, json=test_case['data'])
            if response.status_code == 200:
                result = response.json()
                category = result.get('decision', 'Unknown')
                confidence = result.get('confidence', 0)
                print(f"Result: {category} ({confidence:.1%})")
            else:
                print(f"Error: {response.status_code}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    print("🧪 Testing Email Classification Fixes")
    print("=" * 60)
    
    # Test the main Paperpal issue
    success = test_paperpal_email()
    
    # Test other examples
    test_other_examples()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ MAIN ISSUE RESOLVED: Paperpal email is now correctly classified!")
    else:
        print("❌ MAIN ISSUE PERSISTS: Further investigation needed")