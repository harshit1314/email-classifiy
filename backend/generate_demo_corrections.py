"""
Generate sample misclassification data for performance dashboard demo
This creates realistic corrections to populate the confusion matrix
"""
import sqlite3
import random

# Connect to database
conn = sqlite3.connect('email_classifications.db')
cursor = conn.cursor()

# Get some emails to create realistic misclassifications
cursor.execute('''
    SELECT id, category 
    FROM classifications 
    WHERE user_corrected_category IS NULL
    LIMIT 30
''')
emails = cursor.fetchall()

# Define realistic misclassification patterns
# Format: (predicted_wrong, actual_correct)
misclassification_patterns = [
    ('finance', 'hr'),
    ('finance', 'it'),
    ('spam', 'marketing'),
    ('spam', 'social'),
    ('general', 'sales'),
    ('general', 'marketing'),
    ('hr', 'general'),
    ('marketing', 'spam'),
    ('social', 'spam'),
    ('it', 'hr'),
]

print("Creating realistic misclassification corrections...")
print("=" * 70)

corrections_made = 0
for email_id, current_category in emails[:20]:
    # Pick a random misclassification pattern
    pattern = random.choice(misclassification_patterns)
    
    # If the current category matches a predicted category, create a correction
    if current_category == pattern[0]:
        actual_category = pattern[1]
        
        # Update with correction
        cursor.execute('''
            UPDATE classifications
            SET user_corrected_category = ?
            WHERE id = ?
        ''', (actual_category, email_id))
        
        print(f"✅ Email ID {email_id}: {current_category} → {actual_category} (misclassified)")
        corrections_made += 1
        
        if corrections_made >= 12:
            break

conn.commit()

print("=" * 70)
print(f"✅ Created {corrections_made} misclassification corrections")
print("\nNow refresh your Performance dashboard to see:")
print("  • Confusion matrix filled with data")
print("  • Precision, Recall, F1-scores calculated")
print("  • Misclassified emails list populated")

# Show summary
cursor.execute('''
    SELECT category, user_corrected_category, COUNT(*)
    FROM classifications
    WHERE user_corrected_category IS NOT NULL
    AND user_corrected_category != category
    GROUP BY category, user_corrected_category
''')
results = cursor.fetchall()

print("\nConfusion Matrix Preview:")
print("-" * 70)
for predicted, actual, count in results:
    print(f"  Predicted: {predicted:12} → Actual: {actual:12} | Count: {count}")

conn.close()
print("\n✅ Done! Refresh the Performance page now!")
