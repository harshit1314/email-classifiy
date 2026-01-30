# Model Retraining Fix - Critical Issue Report

## Issue Identified

The **Model Retraining** functionality in the Settings page has a critical bug:
- ❌ It retrains the **OLD** TF-IDF + Naive Bayes model (`email_classifier_model.joblib`)
- ❌ It does NOT retrain the **NEW** Improved Ensemble Classifier (`improved_classifier_model.joblib`)
- ❌ This means all retraining efforts are wasted on the old, less accurate model

## Root Cause

Location: `backend/app/services/retraining_service.py` lines 110-125

```python
# CURRENT CODE (WRONG):
def retrain_model(self, user_id: Optional[int] = None, use_feedback: bool = True) -> Dict:
    # ... gets training data ...
    
    # Initialize classifier (will use TF-IDF as fallback)
    self.classifier = EmailClassifier(use_bert=False, use_llm=False)  # ❌ OLD MODEL
    
    # Create new pipeline
    model = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
        ('clf', MultinomialNB())  # ❌ OLD ALGORITHM
    ])
    
    # Train the model
    model.fit(texts, labels)
    
    # Save the model
    model_path = os.path.join(os.path.dirname(__file__), '..', 'ml', 'email_classifier_model.joblib')
    joblib.dump(model, model_path)  # ❌ SAVES TO OLD MODEL FILE
```

## The Fix

Replace the retraining logic to use the **Improved Classifier**:

```python
# FIXED CODE:
def retrain_model(self, user_id: Optional[int] = None, use_feedback: bool = True) -> Dict:
    # ... gets training data ...
    
    # Import the improved classifier
    from app.ml.improved_classifier import ImprovedEmailClassifier
    
    # Initialize improved classifier
    classifier = ImprovedEmailClassifier()
    
    # Train with feedback data
    result = classifier.train_model_with_data(texts, labels)
    
    # The improved classifier automatically saves to the correct path
    model_path = os.path.join(os.path.dirname(__file__), '..', 'ml', 'improved_classifier_model.joblib')
    
    return {
        "success": True,
        "message": "Improved model retrained successfully",
        "samples_count": len(texts),
        "feedback_samples": feedback_count,
        "category_distribution": category_counts,
        "accuracy": result.get('accuracy', 'N/A'),
        "timestamp": datetime.now().isoformat()
    }
```

## Impact

### Current State (BROKEN):
- ✅ Settings page UI works correctly
- ✅ Retraining status endpoint works
- ✅ API calls succeed
- ❌ **BUT**: Retrains the wrong model (old TF-IDF)
- ❌ **Result**: No improvement in classification accuracy

### After Fix:
- ✅ Settings page UI works correctly
- ✅ Retraining status endpoint works
- ✅ API calls succeed
- ✅ **Retrains the correct model** (improved ensemble)
- ✅ **Result**: Real classification improvement from user feedback

## Verification Steps

After fixing:

1. **Test via Settings Page:**
   - Go to Settings → AI Model tab
   - Click "Start Retraining"
   - Should see success message

2. **Verify Model File:**
   ```bash
   # Check if improved model was updated
   ls -l backend/app/ml/improved_classifier_model.joblib
   ```

3. **Test Classification:**
   ```bash
   python backend/test_security_email.py
   ```
   Should still show 61.9% confidence for "work" category

## Files to Modify

1. `backend/app/services/retraining_service.py` - Lines 110-145
   - Change from TF-IDF/NaiveBayes to ImprovedEmailClassifier
   - Update model save path
   - Add accuracy metrics to return value

2. Optional: `backend/app/ml/improved_classifier.py` - Add helper method
   - Add `train_model_with_data(texts, labels)` method
   - Makes retraining easier from external services

## Current Accuracy

**Improved Classifier (88.9% test accuracy):**
- ✅ IT Security Advisory → work (61.9%)
- ✅ Spam detection (78.6%)
- ✅ Promotions (70.3%)
- ✅ Work emails (74.7%)

**Old TF-IDF Model (~60% accuracy):**
- ❌ Much lower accuracy
- ❌ No domain-specific features
- ❌ No ensemble methods

## Recommendation

**CRITICAL**: Fix the retraining service ASAP to use the improved classifier. Otherwise, all user feedback and retraining efforts are wasted on the old, less accurate model.

The Settings page UI is working fine - it's just calling the wrong backend logic.
