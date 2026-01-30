"""
Reclassify all existing emails with the new trained model
"""
import sqlite3
import joblib
import os

# Define the custom pipeline class (needed to unpickle the model)
class GradientBoostingPipeline:
    """Wrapper for GradientBoosting classifier with vectorizer"""
    def __init__(self, vectorizer, classifier, label_encoder):
        self.vectorizer = vectorizer
        self.classifier = classifier
        self.label_encoder = label_encoder
    
    def predict(self, X):
        X_vec = self.vectorizer.transform(X)
        y_encoded = self.classifier.predict(X_vec)
        return self.label_encoder.inverse_transform(y_encoded)
    
    def predict_proba(self, X):
        X_vec = self.vectorizer.transform(X)
        return self.classifier.predict_proba(X_vec)

def reclassify_all_emails():
    """Reclassify all emails in database with new model"""
    print("=" * 70)
    print("🔄 RECLASSIFYING EMAILS WITH TRAINED MODEL")
    print("=" * 70)
    print()
    
    # Load the trained model
    model_path = os.path.join(os.path.dirname(__file__), 'app', 'ml', 'improved_classifier_model.joblib')
    
    if not os.path.exists(model_path):
        print(f"❌ Trained model not found at: {model_path}")
        return
    
    print(f"📦 Loading trained model from: {model_path}")
    classifier = joblib.load(model_path)
    print("✅ Model loaded successfully")
    print()
    
    # Connect to SQLite database
    db_path = os.path.join(os.path.dirname(__file__), 'email_classifications.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return
    
    print(f"📂 Connecting to database: {db_path}")
    conn = sqlite3.Connection(db_path)
    cursor = conn.cursor()
    print()
    
    # Get all emails
    print("📥 Fetching all emails from database...")
    cursor.execute("SELECT id, email_subject, email_body FROM classifications WHERE email_subject IS NOT NULL")
    all_emails = cursor.fetchall()
    
    if not all_emails:
        print("⚠️  No emails found in database")
        conn.close()
        return
    
    print(f"✅ Found {len(all_emails)} emails")
    print()
    
    # Reclassify each email
    print("🔄 Reclassifying emails...")
    print()
    
    updated_count = 0
    error_count = 0
    
    for i, (email_id, subject, body) in enumerate(all_emails, 1):
        try:
            if not subject and not body:
                continue
            
            # Classify with new model
            text = f"{subject or ''} {body or ''}"
            predicted_category = classifier.predict([text])[0]
            
            # Get confidence
            if hasattr(classifier, 'predict_proba'):
                proba = classifier.predict_proba([text])[0]
                confidence = float(max(proba))
            else:
                confidence = 0.85
            
            # Update in database
            cursor.execute(
                "UPDATE classifications SET category = ?, confidence = ? WHERE id = ?",
                (predicted_category, confidence, email_id)
            )
            
            updated_count += 1
            
            if i % 10 == 0:
                print(f"  Processed {i}/{len(all_emails)} emails...")
            
        except Exception as e:
            error_count += 1
            print(f"  ⚠️  Error processing email {email_id}: {e}")
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print()
    print("=" * 70)
    print("✅ RECLASSIFICATION COMPLETE")
    print("=" * 70)
    print()
    print(f"✅ Successfully reclassified: {updated_count} emails")
    if error_count > 0:
        print(f"⚠️  Errors: {error_count} emails")
    print()
    print("🔄 Please refresh your browser to see the updated categories!")
    print()

if __name__ == "__main__":
    reclassify_all_emails()
