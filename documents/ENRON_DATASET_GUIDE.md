# 📧 Enron Email Dataset Integration

## Overview

The Enron Email Dataset contains approximately 500,000 real emails from Enron Corporation executives. This dataset is excellent for training and testing email classification models.

## Prerequisites

1. **Kaggle Account**: Create account at [kaggle.com](https://kaggle.com)
2. **Kaggle API Credentials**:
   - Go to Kaggle Settings → API → Create New API Token
   - Download `kaggle.json`
   - Place it in:
     - **Windows**: `C:\Users\<username>\.kaggle\kaggle.json`
     - **Linux/Mac**: `~/.kaggle/kaggle.json`

## Installation

Install required package:
```bash
pip install kagglehub
```

Or install all dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Step 1: Download Dataset

```bash
cd backend
python download_enron_dataset.py
```

This will:
- Download the Enron dataset from Kaggle (~1.5GB)
- Save the dataset location to `enron_dataset_path.txt`
- Show dataset structure and files

### Step 2: Process Emails

```bash
python process_enron_dataset.py
```

This will:
- Parse emails from maildir format
- Extract subject, body, sender, and metadata
- Save processed emails to CSV:
  - `enron_emails_processed.csv` - Full dataset (10,000 emails)
  - `enron_emails_processed_sample.csv` - Quick sample (1,000 emails)

### Step 3: Use for Training

The processed CSV files can be used to:

1. **Train new models**:
   ```python
   import pandas as pd
   from app.ml.improved_classifier import ImprovedEmailClassifier
   
   df = pd.read_csv('enron_emails_processed.csv')
   # Add category labels
   # Train model with real data
   ```

2. **Test classification accuracy**:
   ```python
   # Use sample for quick testing
   df = pd.read_csv('enron_emails_processed_sample.csv')
   classifier = EmailClassifier()
   
   for _, row in df.iterrows():
       result = classifier.classify(row['subject'], row['body'])
       print(f"Subject: {row['subject'][:50]}")
       print(f"Category: {result['category']}")
   ```

3. **Expand training data**:
   - Mix Enron emails with your existing training data
   - Improve model accuracy with real-world examples
   - Test edge cases and unusual email formats

## Dataset Structure

```
enron-email-dataset/
├── maildir/               # Main email directory
│   ├── user1/
│   │   ├── inbox/
│   │   ├── sent/
│   │   ├── deleted_items/
│   │   └── ...
│   ├── user2/
│   └── ...
```

Each email is stored as a plain text file in standard maildir format with headers and body.

## Configuration

### Adjust Processing Limits

Edit `process_enron_dataset.py`:
```python
# Process more or fewer emails
df = process_enron_dataset(dataset_path, max_emails=50000)  # Default: 10000
```

### Custom Filtering

Add filters to `parse_email_file()` function:
```python
# Skip emails without proper subject
if not subject or len(subject) < 5:
    return None

# Skip automated emails
if 'automated' in subject.lower():
    return None
```

## Data Format

Processed CSV columns:
- `subject`: Email subject line
- `body`: Email body content (cleaned)
- `sender`: Sender email address

You'll need to add:
- `category`: Manual or automatic categorization (spam, important, etc.)
- `priority`: Optional priority level

## Integration with Your Classifier

### Manual Labeling

1. Load processed emails
2. Review and add category labels
3. Save labeled dataset
4. Use for training

### Automatic Pre-labeling

Use your existing classifier to pre-label:
```python
import pandas as pd
from app.ml.classifier import EmailClassifier

df = pd.read_csv('enron_emails_processed.csv')
classifier = EmailClassifier()

# Pre-label with existing model
categories = []
for _, row in df.iterrows():
    result = classifier.classify(row['subject'], row['body'])
    categories.append(result['category'])

df['category'] = categories
df.to_csv('enron_emails_labeled.csv', index=False)
```

Then manually review and correct labels.

## Benefits

✅ **Real-world data**: Actual business emails from a real company
✅ **Large volume**: 500,000+ emails for comprehensive training
✅ **Diverse content**: Various types of business communications
✅ **Well-structured**: Standard email format with headers
✅ **Free access**: Open dataset available through Kaggle

## Tips

1. **Start small**: Process 1,000-10,000 emails first to test
2. **Manual review**: Review sample emails before bulk processing
3. **Balance categories**: Ensure even distribution across categories
4. **Incremental training**: Retrain models with new data periodically
5. **Validate results**: Test accuracy on held-out test set

## Troubleshooting

**Kaggle API Error**:
- Ensure `kaggle.json` is in correct location
- Check file permissions (should be readable)
- Verify Kaggle account is active

**Memory Issues**:
- Reduce `max_emails` parameter
- Process in batches
- Use sample file for testing

**Parsing Errors**:
- Some emails may have encoding issues
- Script handles errors gracefully
- Check console output for skipped files

## Next Steps

1. ✅ Download dataset
2. ✅ Process emails
3. ⬜ Add category labels
4. ⬜ Train improved model
5. ⬜ Validate accuracy
6. ⬜ Deploy to production

## References

- Dataset: [Kaggle Enron Email Dataset](https://www.kaggle.com/datasets/wcukierski/enron-email-dataset)
- Format: Maildir (standard Unix mail format)
- License: Public domain
