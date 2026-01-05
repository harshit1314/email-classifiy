# ML package - Email Classification Models

# Primary: Enterprise Classifier (department routing for companies)
from .enterprise_classifier import EnterpriseEmailClassifier

# Secondary: DistilBERT (lightweight, fast, no training needed)
from .distilbert_classifier import DistilBERTEmailClassifier

# Backward compatibility - BERTEmailClassifier now uses DistilBERT
from .distilbert_classifier import BERTEmailClassifier, EmailClassifier

