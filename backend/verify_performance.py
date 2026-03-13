import sys
sys.path.insert(0, '.')
from app.services.performance_service import PerformanceService

ps = PerformanceService()
summary = ps.get_performance_summary()
print("accuracy:", summary["accuracy"])
print("total_corrections:", summary["total_corrections"])
print("weighted_f1_score:", summary["weighted_f1_score"])

cm = ps.calculate_confusion_matrix()
print("confusion_matrix_corrections:", cm["total_corrections"])
print("categories:", cm["categories"])

mis = ps.get_misclassified_emails(limit=5)
print("misclassified_emails:", len(mis))
for m in mis[:3]:
    subj = (m["subject"] or "")[:40]
    print(f"  predicted={m['predicted']} | actual={m['actual']} | {subj}")
