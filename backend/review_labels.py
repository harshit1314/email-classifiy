"""
Review and fix training labels manually
Shows predictions vs auto-labels to identify errors
"""
import pandas as pd
import joblib
import os

def review_labels():
    """Review auto-generated labels and fix errors"""
    print("=" * 70)
    print("📋 LABEL REVIEW & CORRECTION")
    print("=" * 70)
    print()
    
    # Load labeled dataset
    csv_path = 'enron_emails_labeled.csv'
    if not os.path.exists(csv_path):
        print("❌ No labeled dataset found. Run training first.")
        return
    
    df = pd.read_csv(csv_path)
    print(f"✅ Loaded {len(df)} labeled emails")
    print()
    
    # Load trained model
    model_path = 'app/ml/improved_classifier_model.joblib'
    if os.path.exists(model_path):
        classifier = joblib.load(model_path)
        print(f"✅ Loaded trained model")
    else:
        print("⚠️  No trained model found, using keywords only")
        classifier = None
    print()
    
    # Find potential labeling errors
    print("🔍 Finding potential labeling errors...")
    print()
    
    if classifier:
        # Predict with model
        df['predicted'] = classifier.predict(df['subject'] + ' ' + df['body'])
        
        # Find mismatches
        mismatches = df[df['category'] != df['predicted']]
        print(f"Found {len(mismatches)} potential errors ({len(mismatches)/len(df)*100:.1f}%)")
        print()
        
        # Show top mismatches
        print("Top 20 potential errors:")
        print("-" * 70)
        
        for i, row in mismatches.head(20).iterrows():
            print(f"\nEmail #{i}:")
            print(f"  Subject: {row['subject'][:60]}...")
            print(f"  Keyword Label: {row['category']}")
            print(f"  Model Says: {row['predicted']}")
            print(f"  Body preview: {row['body'][:100]}...")
            
            # Ask for correction
            choice = input("\n  Keep keyword label (k), use model (m), or enter correct category: ").strip().lower()
            
            if choice == 'm':
                df.at[i, 'category'] = row['predicted']
                print(f"  ✅ Changed to: {row['predicted']}")
            elif choice == 'k':
                print(f"  ✅ Kept: {row['category']}")
            elif choice in ['finance', 'hr', 'legal', 'it', 'sales', 'operations', 'management', 'general']:
                df.at[i, 'category'] = choice
                print(f"  ✅ Changed to: {choice}")
            elif choice == 'q':
                break
    
    # Save corrected labels
    save = input("\n💾 Save corrected labels? (y/n): ").strip().lower()
    if save == 'y':
        df.to_csv(csv_path, index=False)
        print(f"✅ Saved to: {csv_path}")
        print("\n🔄 Now run training again to train on corrected labels!")
    
if __name__ == "__main__":
    review_labels()
