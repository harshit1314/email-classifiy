# Email Classification Implementation Details

This document outlines the architecture, algorithms, and implementation details for the AI Email Classifier's Core Classification Engine.

## Overview

The classification engine analyzes incoming emails (subject line, body, sender) and determines the appropriate departmental category: `HR`, `Finance`, `Sales`, `Marketing`, or `Support`.

The system utilizes a hybrid approach:
1. **Primary AI Brain**: A Transformer-based DistilBERT zero-shot classifier.
2. **Fallback Logic**: TF-IDF vectorization with traditional Machine Learning models (Logistic Regression, Random Forest, Naive Bayes).

## 1. DistilBERT Zero-Shot Classification (Primary)

The primary model is `distilbert-base-uncased-mnli`. Unlike traditional models that require thousands of labeled examples to train, this leverages **Natural Language Inference (NLI)** to classify text without specific fine-tuning for our departments.

### How Zero-Shot Works in our Implementation
The pipeline tests hypothesis statements. For an email about paychecks, the model compares the email text against hypotheses like *"This example is HR"*, *"This example is Finance"*, etc., and generates an entailment probability.

### Code Implementation (`distilbert_classifier.py`)

```python
from transformers import pipeline

class DistilBERTEmailClassifier:
    def __init__(self):
        self.categories = ["HR", "Finance", "Sales", "Marketing", "Support"]
        # Load the zero-shot classification pipeline
        self.classifier = pipeline(
            "zero-shot-classification", 
            model="distilbert-base-uncased-mnli"
        )
        
        # Keyword boosting dictionaries for dynamic retraining
        self.keywords = {
            "HR": ["payroll", "leave", "onboarding", "benefits", "vacation"],
            "Finance": ["invoice", "budget", "expense", "tax", "payment"],
            "Sales": ["contract", "lead", "quota", "deal", "pricing"],
            "Marketing": ["campaign", "social media", "seo", "branding"],
            "Support": ["bug", "error", "broken", "help", "login"]
        }

    def predict(self, text):
        """Classifies the text into one of the departments"""
        # Run zero-shot pipeline
        result = self.classifier(text, self.categories, multi_label=False)
        
        # Extract top category and confidence
        top_category = result['labels'][0]
        confidence = result['scores'][0]
        
        # Apply keyword boosting manually
        top_category, confidence = self._apply_keyword_boosting(text, top_category, confidence, result)
        
        return {
            "category": top_category,
            "confidence": float(confidence),
            "probabilities": {label: score for label, score in zip(result['labels'], result['scores'])}
        }
```

## 2. Dynamic Keyword Boosting (Retraining)

Traditional HuggingFace models are expensive to fine-tune. To achieve continuous learning, we use **Keyword Boosting**. 

When a user corrects a misclassified email in the dashboard:
1. The `RetrainingService` extracts unique terms from the email using TF-IDF.
2. These new terms are appended to the `self.keywords` dictionary in the DistilBERT class.
3. The `_apply_keyword_boosting` method intercepts the raw DistilBERT probability and adds weights if specific keywords are found.

### Boosting Logic Snippet
```python
def _apply_keyword_boosting(self, text, current_top_label, current_confidence, raw_result):
    text_lower = text.lower()
    
    # Calculate keyword matches per category
    boost_scores = {}
    for category, category_keywords in self.keywords.items():
        matches = sum(1 for kw in category_keywords if kw in text_lower)
        # Assign a small probability bump per matched keyword
        boost_scores[category] = matches * 0.05 
        
    # Recalculate probabilities
    # ... (applies the boost to the raw huggingface scores and returns the new highest label)
```

## 3. Fallback Classifier (TF-IDF & Classical ML)

If the server lacks memory for the transformer model, the processing service fails over to `ImprovedEmailClassifier`.

### Implementation (`improved_classifier.py`)
This implementation vectorizes the Enron dataset subset using `TfidfVectorizer` and trains either a `LogisticRegression` or `RandomForestClassifier`.

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline

class ImprovedEmailClassifier:
    def __init__(self):
        # Create a machine learning pipeline
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                max_features=5000,
                ngram_range=(1, 2), # Use unigrams and bigrams
                stop_words='english'
            )),
            ('clf', RandomForestClassifier(n_estimators=100))
        ])
        
    def train(self, historical_emails_x, labels_y):
        self.pipeline.fit(historical_emails_x, labels_y)
        
    def predict(self, text):
        category = self.pipeline.predict([text])[0]
        confidence = max(self.pipeline.predict_proba([text])[0])
        return {"category": category, "confidence": confidence}
```

## 4. Orchestration (`ProcessingService`)

The `ProcessingService` wraps the ML logic, formatting the inputs (subject + body) and aggregating the results with Sentiment Analysis and Entity Extraction.

```python
async def analyze_email(self, subject: str, body: str, sender: str = None) -> Dict:
    combined_text = f"{subject}\n\n{body}"
    
    # 1. Run Classification
    classification = self.classifier.predict(combined_text)
    
    # 2. Run Sentiment 
    sentiment = self.sentiment_service.analyze(combined_text)
    
    # 3. Formulate response
    return {
        "decision": classification["category"],
        "confidence": classification["confidence"],
        "sentiment": sentiment
    }
```
