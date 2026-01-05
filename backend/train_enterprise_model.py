"""
Train Enterprise Email Classifier with Curated Dataset
This script loads the training data and fine-tunes the model
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ml.enterprise_classifier import EnterpriseEmailClassifier
from app.ml.training_data import ENTERPRISE_TRAINING_DATA, get_training_stats


def load_curated_data(classifier: EnterpriseEmailClassifier) -> int:
    """Load the curated training dataset"""
    print("\n📚 Loading curated training data...")
    
    examples = []
    for subject, body, department in ENTERPRISE_TRAINING_DATA:
        examples.append({
            "subject": subject,
            "body": body,
            "department": department
        })
    
    added = classifier.add_training_examples_bulk(examples)
    print(f"✅ Loaded {added} training examples")
    
    return added


def show_stats(classifier: EnterpriseEmailClassifier):
    """Display training data statistics"""
    stats = classifier.get_training_stats()
    
    print("\n📊 Training Data Statistics:")
    print(f"   Total Examples: {stats['total_examples']}")
    print(f"   Fine-tuned: {stats['is_fine_tuned']}")
    print(f"   Ready to train: {stats['ready_to_fine_tune']}")
    
    print("\n   By Department:")
    for dept, count in sorted(stats['by_department'].items(), key=lambda x: -x[1]):
        bar = "█" * (count // 3)
        print(f"     {dept:20s}: {count:4d} {bar}")


def train_model(classifier: EnterpriseEmailClassifier, epochs: int = 3):
    """Fine-tune the model"""
    print(f"\n🚀 Starting fine-tuning with {epochs} epochs...")
    print("   This may take 5-15 minutes depending on your hardware...\n")
    
    result = classifier.fine_tune(epochs=epochs, batch_size=16, learning_rate=3e-5)
    
    if result["success"]:
        print(f"\n✅ Training Complete!")
        print(f"   Examples used: {result['examples_used']}")
        print(f"   Model saved to: {result['model_saved_to']}")
    else:
        print(f"\n❌ Training Failed: {result['error']}")
    
    return result


def test_model(classifier: EnterpriseEmailClassifier):
    """Test the trained model"""
    print("\n🧪 Testing trained model...\n")
    
    test_emails = [
        ("Need pricing for 50 licenses", "We're interested in purchasing your software for our team.", "Expected: sales"),
        ("Job Application - Software Developer", "Please find my resume attached for the open position.", "Expected: hr"),
        ("Invoice #INV-2024-5678", "Please find attached the invoice for Q4 services.", "Expected: finance"),
        ("Can't login to my computer", "My password isn't working and I'm locked out.", "Expected: it_support"),
        ("Contract Review Needed", "Please review the attached NDA before we proceed.", "Expected: legal"),
        ("Q1 Campaign Results", "Here are the analytics from our latest marketing campaign.", "Expected: marketing"),
        ("Complaint about order #12345", "The product arrived damaged and I want a refund.", "Expected: customer_service"),
        ("Shipping delay notification", "Your order shipment has been delayed by 3 days.", "Expected: operations"),
        ("Board Meeting Agenda", "Please review the agenda for next week's board meeting.", "Expected: executive"),
    ]
    
    correct = 0
    for subject, body, expected in test_emails:
        result = classifier.classify(subject, body)
        predicted = result['department']
        confidence = result['confidence']
        expected_dept = expected.replace("Expected: ", "")
        
        status = "✅" if predicted == expected_dept else "❌"
        if predicted == expected_dept:
            correct += 1
        
        print(f"{status} {subject[:40]:40s} → {predicted:18s} ({confidence:.1%}) {expected}")
    
    accuracy = correct / len(test_emails) * 100
    print(f"\n📊 Test Accuracy: {accuracy:.0f}% ({correct}/{len(test_emails)})")


def main():
    print("=" * 60)
    print("🏢 Enterprise Email Classifier Training")
    print("=" * 60)
    
    # Initialize classifier
    print("\n🔧 Initializing classifier...")
    classifier = EnterpriseEmailClassifier()
    
    # Check current status
    show_stats(classifier)
    
    # Load curated data if not already loaded
    stats = classifier.get_training_stats()
    if stats['total_examples'] < 500:
        load_curated_data(classifier)
        show_stats(classifier)
    else:
        print("\n✅ Training data already loaded")
    
    # Ask user if they want to train
    print("\n" + "=" * 60)
    response = input("\n🤔 Do you want to fine-tune the model? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        epochs = input("   Number of epochs (default 3): ").strip()
        epochs = int(epochs) if epochs.isdigit() else 3
        
        result = train_model(classifier, epochs=epochs)
        
        if result["success"]:
            # Test the model
            test_model(classifier)
    else:
        print("\n📝 Training data has been loaded but model is not fine-tuned yet.")
        print("   You can fine-tune later via the API or by running this script again.")
        
        # Test with zero-shot
        print("\n🧪 Testing with zero-shot model (without fine-tuning)...")
        test_model(classifier)
    
    print("\n" + "=" * 60)
    print("✨ Done!")


if __name__ == "__main__":
    main()
