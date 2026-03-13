"""
DB Repair Script: Restore original ML category for corrupted corrections.
The old bug set category = user_corrected_category (both the same).
This script restores category = original_category from user_feedback table,
so performance_service can correctly detect misclassifications.
"""
import sqlite3

conn = sqlite3.connect('email_classifications.db')
cursor = conn.cursor()

print("=" * 60)
print("DB REPAIR: Restoring original categories from user_feedback")
print("=" * 60)

# Get the most recent original_category for each classification from user_feedback
# (earliest feedback entry = first correction = original ML category)
cursor.execute("""
    SELECT classification_id, original_category, corrected_category
    FROM user_feedback
    ORDER BY timestamp ASC
""")
feedback_rows = cursor.fetchall()

# Build mapping: classification_id -> first original_category
first_originals = {}
for cls_id, orig, corrected in feedback_rows:
    if cls_id not in first_originals:
        first_originals[cls_id] = orig

print(f"\nFound {len(first_originals)} unique classification IDs in user_feedback")

# Find corrupted rows (category == user_corrected_category)
cursor.execute("""
    SELECT id, category, user_corrected_category
    FROM classifications
    WHERE user_corrected_category IS NOT NULL 
    AND user_corrected_category != ''
    AND user_corrected_category = category
""")
corrupted = cursor.fetchall()
print(f"Found {len(corrupted)} corrupted rows (category == user_corrected_category)")

repaired = 0
skipped = 0
for row in corrupted:
    cls_id, current_category, user_corrected = row
    
    if cls_id in first_originals:
        original = first_originals[cls_id]
        if original != user_corrected:
            cursor.execute("""
                UPDATE classifications SET category = ?
                WHERE id = ?
            """, (original, cls_id))
            print(f"  Repaired id={cls_id}: restored category='{original}' (was overwritten with '{user_corrected}')")
            repaired += 1
        else:
            # user_corrected is same as original - this was a no-op correction
            print(f"  Skipped id={cls_id}: original='{original}' == corrected='{user_corrected}' (no-op correction)")
            skipped += 1
    else:
        print(f"  No user_feedback entry for id={cls_id}, cannot recover original category")
        skipped += 1

conn.commit()

print(f"\n{'='*60}")
print(f"Repaired: {repaired} rows")
print(f"Skipped:  {skipped} rows (no recovery data)")
print(f"{'='*60}")

# Verify
cursor.execute("""
    SELECT COUNT(*) FROM classifications 
    WHERE user_corrected_category IS NOT NULL 
    AND user_corrected_category != ''
    AND user_corrected_category != category
""")
visible = cursor.fetchone()[0]
print(f"\nCorrections now VISIBLE to performance page: {visible}")

conn.close()
