import requests
import json

def verify():
    print("Verifying API stats...")
    try:
        # Login
        url = "http://127.0.0.1:8000"
        auth_url = f"{url}/api/auth/login"
        creds = {"email": "admin@emailclassifier.com", "password": "admin123"}
        response = requests.post(auth_url, json=creds)
        token = response.json().get("access_token")
        
        if not token:
            print("Login failed")
            return
            
        headers = {"Authorization": f"Bearer {token}"}
        
        # Check by-department analytics
        stats_url = f"{url}/api/analytics/by-department"
        response = requests.get(stats_url, headers=headers)
        data = response.json()
        
        print("\nAPI Department Statistics:")
        stats = data.get("department_statistics", {})
        for dept_key, info in stats.items():
            print(f"  {dept_key}: {info.get('total')}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify()
