"""Quick test of the fine-tuned enterprise classifier"""
from app.ml.enterprise_classifier import EnterpriseEmailClassifier

clf = EnterpriseEmailClassifier()
print(f"Model: {'Fine-tuned ✅' if clf.is_fine_tuned else 'Zero-shot'}")
print("=" * 70)

tests = [
    ("Sales", "Request for Quote - 500 licenses", "We need pricing for enterprise software"),
    ("HR", "Job Application - Software Engineer", "Please find my resume attached"),
    ("Finance", "Invoice #2024-1234", "Payment due for Q4 services rendered"),
    ("IT Support", "Password reset needed", "I forgot my password and locked out"),
    ("Legal", "Contract Review Request", "Please review the attached vendor agreement"),
    ("Marketing", "Campaign Performance Report", "Here are the Q1 social media analytics"),
    ("Customer Service", "Terrible Experience!!!", "Product arrived damaged. Want refund!"),
    ("Operations", "Shipment Delay Notice", "Warehouse inventory is running low"),
    ("Executive", "Board Meeting - Confidential", "Strategic acquisition requires board approval"),
    ("General", "Office Party Friday", "Don't forget the team lunch celebration"),
]

for expected, subject, body in tests:
    result = clf.classify(subject, body)
    dept = result['department']
    conf = result['confidence']
    match = "✅" if dept.lower().replace("_", " ") in expected.lower() or expected.lower() in dept else "❌"
    print(f"{match} {expected:16} → {dept:18} ({conf:5.1%}) | {subject[:35]}")

print("=" * 70)
