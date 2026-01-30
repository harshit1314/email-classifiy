"""
Download and prepare Enron Email Dataset from Kaggle
This dataset contains real emails that can be used for training/testing the classifier
"""
import os
import sys

def setup_kaggle_auth():
    """Setup Kaggle authentication"""
    # Check if KAGGLE_API_TOKEN is set
    if 'KAGGLE_API_TOKEN' not in os.environ:
        print("⚠️  KAGGLE_API_TOKEN not found in environment variables")
        print()
        print("You can set it by running:")
        print("  Windows (PowerShell): $env:KAGGLE_API_TOKEN='your_token_here'")
        print("  Mac/Linux: export KAGGLE_API_TOKEN='your_token_here'")
        print()
        print("Or place kaggle.json in ~/.kaggle/ directory")
        print()
        
        # Ask if user wants to set it now
        token = input("Enter your Kaggle API token (or press Enter to skip): ").strip()
        if token:
            os.environ['KAGGLE_API_TOKEN'] = token
            print("✅ Token set for this session")
        else:
            print("⚠️  Continuing without token - may fail if kaggle.json not found")
    else:
        print("✅ Kaggle API token found in environment")

def download_dataset():
    """Download Enron dataset from Kaggle"""
    try:
        import kagglehub
    except ImportError:
        print("❌ kagglehub not installed. Installing...")
        os.system(f"{sys.executable} -m pip install kagglehub")
        import kagglehub
    
    print("=" * 70)
    print("📥 Downloading Enron Email Dataset from Kaggle")
    print("=" * 70)
    print()
    print("This dataset contains ~500,000 emails from Enron Corporation")
    print("Perfect for training and testing email classification models")
    print()
    
    # Setup authentication
    setup_kaggle_auth()
    
    # Download latest version
    print("⏳ Downloading... (this may take a few minutes)")
    path = kagglehub.dataset_download("wcukierski/enron-email-dataset")
    
    print()
    print("✅ Download complete!")
    print(f"📁 Dataset location: {path}")
    print()
    
    # List files in the dataset
    print("📂 Dataset files:")
    for root, dirs, files in os.walk(path):
        level = root.replace(path, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 2 * (level + 1)
        for file in files[:10]:  # Show first 10 files
            print(f'{subindent}{file}')
        if len(files) > 10:
            print(f'{subindent}... and {len(files) - 10} more files')
    
    print()
    print("=" * 70)
    print("🎯 Next Steps:")
    print("=" * 70)
    print("1. Explore the dataset structure")
    print("2. Parse emails for classification")
    print("3. Use for training/testing your models")
    print()
    print("💡 The emails are typically in maildir format")
    print("   You can process them to extract subject, body, sender, etc.")
    print()
    
    return path

if __name__ == "__main__":
    try:
        dataset_path = download_dataset()
        
        # Save path to a file for easy reference
        with open("enron_dataset_path.txt", "w") as f:
            f.write(dataset_path)
        
        print("✅ Dataset path saved to: enron_dataset_path.txt")
        
    except Exception as e:
        print(f"❌ Error downloading dataset: {e}")
        print()
        print("📝 Note: You need Kaggle API credentials")
        print("   1. Create account at kaggle.com")
        print("   2. Go to Settings -> API -> Create New API Token")
        print("   3. Save kaggle.json to ~/.kaggle/ (Linux/Mac) or C:\\Users\\<username>\\.kaggle\\ (Windows)")
        sys.exit(1)
