"""
Model Comparison Service - Train and benchmark multiple ML algorithms
for email classification to justify model selection in BTech project
"""
import sqlite3
import logging
import time
import json
from typing import Dict, List, Tuple
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB, ComplementNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score, cross_validate
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report
import re

logger = logging.getLogger(__name__)

class ModelComparisonService:
    """Service to train, compare, and benchmark multiple ML algorithms"""
    
    def __init__(self, db_path: str = "email_classifications.db"):
        self.db_path = db_path
        self.models = {}
        self.comparison_results = None
        self.training_data = None
        self.test_data = None
        
    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess text"""
        text = text.lower()
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        text = re.sub(r'\S+@\S+', '', text)
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def load_training_data(self, min_samples_per_category: int = 10) -> Tuple[List[str], List[str]]:
        """
        Load email data from database for training
        Returns: (texts, labels)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get emails with their categories (use user_corrected if available, else original category)
        query = '''
            SELECT 
                email_subject,
                email_body,
                COALESCE(user_corrected_category, category) as final_category
            FROM classifications
            WHERE email_subject IS NOT NULL
            AND email_body IS NOT NULL
            AND COALESCE(user_corrected_category, category) NOT IN ('unknown', 'pending', '')
        '''
        
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        if len(rows) < 50:
            logger.warning(f"Only {len(rows)} samples available. Need at least 50 for meaningful comparison.")
            # For demo purposes, we'll continue but with a warning
        
        texts = []
        labels = []
        
        category_counts = {}
        
        for subject, body, category in rows:
            text = self.preprocess_text(f"{subject} {body}")
            if text.strip():  # Only add if text is not empty
                texts.append(text)
                labels.append(category)
                category_counts[category] = category_counts.get(category, 0) + 1
        
        logger.info(f"Loaded {len(texts)} samples across {len(category_counts)} categories")
        logger.info(f"Category distribution: {category_counts}")
        
        # Filter out categories with too few samples
        filtered_texts = []
        filtered_labels = []
        
        for text, label in zip(texts, labels):
            if category_counts[label] >= min_samples_per_category:
                filtered_texts.append(text)
                filtered_labels.append(label)
        
        logger.info(f"After filtering: {len(filtered_texts)} samples")
        
        return filtered_texts, filtered_labels
    
    def initialize_models(self) -> Dict:
        """Initialize all models to compare"""
        self.models = {
            "Naive Bayes (Multinomial)": Pipeline([
                ('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
                ('clf', MultinomialNB(alpha=0.1))
            ]),
            
            "Naive Bayes (Complement)": Pipeline([
                ('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
                ('clf', ComplementNB(alpha=0.1))
            ]),
            
            "Logistic Regression": Pipeline([
                ('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
                ('clf', LogisticRegression(max_iter=1000, C=1.0, random_state=42))
            ]),
            
            "Linear SVM": Pipeline([
                ('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
                ('clf', LinearSVC(C=1.0, max_iter=2000, random_state=42))
            ]),
            
            "Random Forest": Pipeline([
                ('tfidf', TfidfVectorizer(max_features=3000, ngram_range=(1, 2))),
                ('clf', RandomForestClassifier(n_estimators=100, max_depth=20, random_state=42, n_jobs=-1))
            ]),
            
            "Gradient Boosting": Pipeline([
                ('tfidf', TfidfVectorizer(max_features=3000, ngram_range=(1, 2))),
                ('clf', GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42))
            ])
        }
        
        logger.info(f"Initialized {len(self.models)} models for comparison")
        return self.models
    
    def train_and_evaluate_models(self) -> Dict:
        """
        Train all models and evaluate using cross-validation
        Returns comprehensive comparison results
        """
        logger.info("Starting model comparison...")
        
        # Load data
        texts, labels = self.load_training_data()
        
        if len(texts) < 50:
            return {
                "error": "Insufficient training data",
                "samples": len(texts),
                "message": "Need at least 50 samples for meaningful comparison"
            }
        
        # Initialize models
        self.initialize_models()
        
        results = {}
        
        for model_name, model in self.models.items():
            logger.info(f"\nEvaluating {model_name}...")
            
            try:
                # Time the training
                start_time = time.time()
                
                # Perform cross-validation
                cv_scores = cross_validate(
                    model, texts, labels, 
                    cv=min(5, len(set(labels))),  # 5-fold or less if few categories
                    scoring=['accuracy', 'precision_macro', 'recall_macro', 'f1_macro'],
                    n_jobs=-1,
                    return_train_score=False
                )
                
                training_time = time.time() - start_time
                
                # Train on full dataset for inference speed test
                model.fit(texts, labels)
                
                # Test inference speed
                test_sample = texts[:10] if len(texts) >= 10 else texts
                inference_start = time.time()
                _ = model.predict(test_sample)
                inference_time = (time.time() - inference_start) / len(test_sample) * 1000  # ms per sample
                
                results[model_name] = {
                    "accuracy": float(np.mean(cv_scores['test_accuracy'])),
                    "accuracy_std": float(np.std(cv_scores['test_accuracy'])),
                    "precision": float(np.mean(cv_scores['test_precision_macro'])),
                    "recall": float(np.mean(cv_scores['test_recall_macro'])),
                    "f1_score": float(np.mean(cv_scores['test_f1_macro'])),
                    "training_time": round(training_time, 2),
                    "inference_time_ms": round(inference_time, 2),
                    "samples_used": len(texts),
                    "categories": len(set(labels))
                }
                
                logger.info(f"{model_name}: Accuracy={results[model_name]['accuracy']:.3f}, "
                          f"F1={results[model_name]['f1_score']:.3f}")
                
            except Exception as e:
                logger.error(f"Error training {model_name}: {e}")
                results[model_name] = {
                    "error": str(e),
                    "accuracy": 0,
                    "precision": 0,
                    "recall": 0,
                    "f1_score": 0,
                    "training_time": 0,
                    "inference_time_ms": 0
                }
        
        # Add metadata
        self.comparison_results = {
            "models": results,
            "timestamp": datetime.now().isoformat(),
            "dataset_info": {
                "total_samples": len(texts),
                "num_categories": len(set(labels)),
                "categories": list(set(labels))
            },
            "evaluation_method": "5-fold cross-validation"
        }
        
        logger.info("\nModel comparison complete!")
        return self.comparison_results
    
    def get_comparison_summary(self) -> Dict:
        """Get a summary of model comparison results"""
        if not self.comparison_results:
            # Try to train if not already done
            self.train_and_evaluate_models()
        
        if not self.comparison_results or "error" in self.comparison_results:
            return self.comparison_results or {"error": "No comparison results available"}
        
        models = self.comparison_results["models"]
        
        # Find best models
        best_accuracy = max(models.items(), key=lambda x: x[1].get("accuracy", 0))
        best_f1 = max(models.items(), key=lambda x: x[1].get("f1_score", 0))
        fastest_training = min(models.items(), key=lambda x: x[1].get("training_time", float('inf')))
        fastest_inference = min(models.items(), key=lambda x: x[1].get("inference_time_ms", float('inf')))
        
        return {
            **self.comparison_results,
            "best_models": {
                "accuracy": {"name": best_accuracy[0], "score": best_accuracy[1]["accuracy"]},
                "f1_score": {"name": best_f1[0], "score": best_f1[1]["f1_score"]},
                "training_speed": {"name": fastest_training[0], "time": fastest_training[1]["training_time"]},
                "inference_speed": {"name": fastest_inference[0], "time": fastest_inference[1]["inference_time_ms"]}
            }
        }
    
    def get_model_rankings(self) -> List[Dict]:
        """Get models ranked by overall performance"""
        if not self.comparison_results or "error" in self.comparison_results:
            return []
        
        models = self.comparison_results["models"]
        
        # Calculate composite score: weighted F1 (60%), accuracy (40%)
        rankings = []
        for name, metrics in models.items():
            if "error" not in metrics:
                composite_score = (metrics["f1_score"] * 0.6) + (metrics["accuracy"] * 0.4)
                rankings.append({
                    "name": name,
                    "composite_score": round(composite_score, 4),
                    "accuracy": metrics["accuracy"],
                    "f1_score": metrics["f1_score"],
                    "precision": metrics["precision"],
                    "recall": metrics["recall"],
                    "training_time": metrics["training_time"],
                    "inference_time_ms": metrics["inference_time_ms"]
                })
        
        # Sort by composite score descending
        rankings.sort(key=lambda x: x["composite_score"], reverse=True)
        
        return rankings
