#!/usr/bin/env python3
"""
Model Performance Comparison Tool
Compare different email classification models on accuracy, speed, and resource usage
"""
import time
import torch
import psutil
import os
from typing import Dict, List, Tuple
import json
import pandas as pd
from app.ml.distilbert_classifier import DistilBERTEmailClassifier
from app.ml.advanced_email_classifier import AdvancedEmailClassifier, create_best_email_classifier

class ModelComparison:
    """Compare different email classification models"""
    
    def __init__(self):
        self.test_emails = [
            {
                "subject": "URGENT: Your account will be suspended!",
                "body": "Click here immediately to verify your account or it will be suspended. Act now!",
                "sender": "noreply@suspicious.com",
                "expected": "spam"
            },
            {
                "subject": "Board meeting rescheduled - action required",
                "body": "The quarterly board meeting has been moved to tomorrow 2PM. Please confirm attendance ASAP.",
                "sender": "ceo@company.com", 
                "expected": "important"
            },
            {
                "subject": "50% OFF Everything - Limited Time!",
                "body": "Flash sale! Get 50% off all items. Free shipping on orders over $50. Shop now!",
                "sender": "deals@retailstore.com",
                "expected": "promotion"
            },
            {
                "subject": "Birthday party invitation",
                "body": "You're invited to Sarah's birthday party this Saturday at 7PM. Hope to see you there!",
                "sender": "sarah@gmail.com",
                "expected": "social"
            },
            {
                "subject": "Project Alpha milestone update",
                "body": "The development team has completed phase 1 of Project Alpha. Next review meeting is Monday.",
                "sender": "project.manager@company.com",
                "expected": "work"
            }
        ]
        
        self.models = {}
        
    def initialize_models(self, use_cuda: bool = False):
        """Initialize all models for comparison"""
        print("🤖 Initializing models...")
        
        try:
            # DistilBERT model (primary - lightweight and fast)
            print("  • Loading DistilBERT classifier...")
            self.models["DistilBERT"] = DistilBERTEmailClassifier(use_cuda=use_cuda)
            
            # Advanced models
            print("  • Loading RoBERTa classifier...")
            self.models["RoBERTa"] = AdvancedEmailClassifier("roberta", use_cuda)
            
            print("  • Loading DeBERTa classifier...")
            self.models["DeBERTa"] = AdvancedEmailClassifier("deberta", use_cuda)
            
            print("  • Loading Sentence Transformer...")
            self.models["SentenceTransformer"] = AdvancedEmailClassifier("sentence-transformer", use_cuda)
            
            # Best configurations
            print("  • Loading optimized models...")
            self.models["Best-Accuracy"] = create_best_email_classifier("accuracy", use_cuda)
            self.models["Best-Speed"] = create_best_email_classifier("speed", use_cuda)
            self.models["Best-Balanced"] = create_best_email_classifier("balanced", use_cuda)
            
            print("✅ All models initialized!")
            
        except Exception as e:
            print(f"❌ Error initializing models: {e}")
            
    def measure_performance(self, model_name: str, model) -> Dict:
        """Measure model performance on test emails"""
        print(f"📊 Testing {model_name}...")
        
        results = {
            "model": model_name,
            "accuracy": 0,
            "avg_confidence": 0,
            "avg_inference_time": 0,
            "memory_usage_mb": 0,
            "predictions": []
        }
        
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024
        inference_times = []
        correct_predictions = 0
        total_confidence = 0
        
        for i, email in enumerate(self.test_emails):
            try:
                # Measure inference time
                start_time = time.time()
                
                # Get prediction
                if hasattr(model, 'classify'):
                    prediction = model.classify(
                        email["subject"], 
                        email["body"], 
                        email["sender"]
                    )
                else:
                    # Fallback for different API
                    prediction = {"category": "unknown", "confidence": 0.5}
                
                inference_time = time.time() - start_time
                inference_times.append(inference_time)
                
                # Check accuracy
                predicted_category = prediction.get("category", "unknown")
                is_correct = predicted_category == email["expected"]
                if is_correct:
                    correct_predictions += 1
                
                confidence = prediction.get("confidence", 0)
                total_confidence += confidence
                
                results["predictions"].append({
                    "email_idx": i,
                    "expected": email["expected"],
                    "predicted": predicted_category,
                    "confidence": confidence,
                    "correct": is_correct,
                    "inference_time": inference_time
                })
                
                print(f"    Email {i+1}: {email['expected']} → {predicted_category} ({confidence:.1%}) ✅" if is_correct else f"    Email {i+1}: {email['expected']} → {predicted_category} ({confidence:.1%}) ❌")
                
            except Exception as e:
                print(f"    Email {i+1}: Error - {e}")
                results["predictions"].append({
                    "email_idx": i,
                    "expected": email["expected"],
                    "predicted": "error",
                    "confidence": 0,
                    "correct": False,
                    "inference_time": 0
                })
        
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Calculate metrics
        results["accuracy"] = correct_predictions / len(self.test_emails)
        results["avg_confidence"] = total_confidence / len(self.test_emails)
        results["avg_inference_time"] = sum(inference_times) / len(inference_times) if inference_times else 0
        results["memory_usage_mb"] = end_memory - start_memory
        
        return results
    
    def run_comparison(self, use_cuda: bool = False) -> Dict:
        """Run full model comparison"""
        print("🚀 Starting Model Comparison")
        print("=" * 60)
        
        self.initialize_models(use_cuda)
        
        all_results = []
        
        for model_name, model in self.models.items():
            try:
                result = self.measure_performance(model_name, model)
                all_results.append(result)
                print(f"✅ {model_name} completed\n")
            except Exception as e:
                print(f"❌ {model_name} failed: {e}\n")
                continue
        
        return all_results
    
    def print_summary(self, results: List[Dict]):
        """Print comparison summary"""
        print("📈 MODEL COMPARISON SUMMARY")
        print("=" * 80)
        
        # Create comparison table
        df_data = []
        for result in results:
            df_data.append({
                "Model": result["model"],
                "Accuracy": f"{result['accuracy']:.1%}",
                "Avg Confidence": f"{result['avg_confidence']:.1%}",
                "Inference Time (ms)": f"{result['avg_inference_time']*1000:.1f}",
                "Memory Usage (MB)": f"{result['memory_usage_mb']:.1f}"
            })
        
        df = pd.DataFrame(df_data)
        print(df.to_string(index=False))
        
        print("\n🏆 RECOMMENDATIONS:")
        
        # Find best models for different criteria
        best_accuracy = max(results, key=lambda x: x["accuracy"])
        best_speed = min(results, key=lambda x: x["avg_inference_time"])
        best_memory = min(results, key=lambda x: x["memory_usage_mb"])
        
        print(f"• Best Accuracy: {best_accuracy['model']} ({best_accuracy['accuracy']:.1%})")
        print(f"• Fastest: {best_speed['model']} ({best_speed['avg_inference_time']*1000:.1f}ms)")
        print(f"• Most Memory Efficient: {best_memory['model']} ({best_memory['memory_usage_mb']:.1f}MB)")
        
        # Overall recommendation
        print(f"\n💡 OVERALL RECOMMENDATION:")
        
        # Score models based on balanced criteria
        scored_results = []
        for result in results:
            # Normalize scores (higher is better)
            accuracy_score = result["accuracy"]
            speed_score = 1 / (result["avg_inference_time"] + 0.001)  # Avoid div by zero
            memory_score = 1 / (result["memory_usage_mb"] + 1)
            
            # Weighted overall score (accuracy 50%, speed 30%, memory 20%)
            overall_score = (accuracy_score * 0.5 + 
                           speed_score * 0.3 + 
                           memory_score * 0.2)
            
            scored_results.append((result["model"], overall_score, result))
        
        # Sort by overall score
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        print(f"Best Overall Model: {scored_results[0][0]}")
        print(f"Runner-up: {scored_results[1][0]}")
        
    def save_results(self, results: List[Dict], filename: str = "model_comparison_results.json"):
        """Save detailed results to file"""
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"📁 Detailed results saved to {filename}")


def main():
    """Run the model comparison"""
    print("🎯 Advanced Email Classification Model Comparison")
    print("Testing multiple state-of-the-art models against current BERT implementation\n")
    
    # Check if CUDA is available
    use_cuda = torch.cuda.is_available()
    print(f"🖥️  CUDA Available: {use_cuda}")
    if use_cuda:
        print(f"GPU: {torch.cuda.get_device_name(0)}")
    print()
    
    # Run comparison
    comparison = ModelComparison()
    results = comparison.run_comparison(use_cuda)
    
    # Print summary
    comparison.print_summary(results)
    
    # Save detailed results
    comparison.save_results(results)

if __name__ == "__main__":
    main()