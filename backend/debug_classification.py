#!/usr/bin/env python3
"""
Simple debug test for the classification issue
"""
import requests
import json

def debug_classification():
    """Debug the classification response"""
    
    email_data = {
        "subject": "We're delighted to present Paperpal",
        "body": "We're delighted to present Paperpal, the editing tool academics and researchers prefer. Perfect tool for academics.",
        "sender": "team@paperpal.com"
    }
    
    url = "http://127.0.0.1:8000/api/process/classify"
    
    try:
        print("🔍 Debug: Testing Classification API")
        print("-" * 50)
        
        response = requests.post(url, json=email_data)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code != 200:
            print(f"Error Response: {response.text}")
            return
            
        result = response.json()
        
        print("\n📋 Full Response:")
        print(json.dumps(result, indent=2))
        
        # Check key fields
        decision = result.get('decision')
        category = result.get('category')
        confidence = result.get('confidence', 0)
        
        print(f"\n🎯 Key Results:")
        print(f"Decision: {decision}")
        print(f"Category: {category}")
        print(f"Confidence: {confidence:.1%}")
        
        # Check probabilities
        if 'probabilities' in result:
            print(f"\n📊 Probabilities:")
            for cat, prob in result['probabilities'].items():
                print(f"  {cat}: {prob:.1%}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_classification()