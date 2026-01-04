#!/usr/bin/env python3
"""
Quick Hugging Face Model Upload Script
Simplified version - no username prompt
"""
from huggingface_hub import HfApi, create_repo, login
import os
import sys

# Configuration
REPO_NAME = "empathicgateway-intent-classifier"
MODEL_PATH = "backend/urgency_model.joblib"

print("=" * 60)
print("🚀 EmpathicGateway Model Upload to Hugging Face Hub")
print("=" * 60)

# Check if model exists
if not os.path.exists(MODEL_PATH):
    print(f"\n❌ Model file not found: {MODEL_PATH}")
    print("Please train the model first by running:")
    print("  python backend/train_model.py")
    sys.exit(1)

model_size = os.path.getsize(MODEL_PATH) / 1024 / 1024
print(f"\n📦 Model file: {MODEL_PATH} ({model_size:.1f} MB)")

# Login to Hugging Face
print("\n🔐 Logging in to Hugging Face...")
print("If you don't have a token:")
print("  1. Go to https://huggingface.co/settings/tokens")
print("  2. Create a new token with 'write' access")
print("  3. Copy and paste it below")
print()

try:
    login()
    print("✅ Login successful!")
except Exception as e:
    print(f"❌ Login failed: {e}")
    print("\nTry running: huggingface-cli login")
    sys.exit(1)

# Get username from whoami
try:
    api = HfApi()
    user_info = api.whoami()
    username = user_info['name']
    print(f"\n👤 Logged in as: {username}")
except Exception as e:
    print(f"❌ Could not get user info: {e}")
    sys.exit(1)

repo_id = f"{username}/{REPO_NAME}"

# Create repository
print(f"\n📁 Creating repository: {repo_id}")
try:
    create_repo(repo_id, repo_type="model", exist_ok=True)
    print(f"✅ Repository ready: https://huggingface.co/{repo_id}")
except Exception as e:
    print(f"⚠️  Repository might already exist: {e}")

# Upload model
print(f"\n📤 Uploading model...")
try:
    api.upload_file(
        path_or_fileobj=MODEL_PATH,
        path_in_repo="urgency_model.joblib",
        repo_id=repo_id,
        repo_type="model"
    )
    print(f"\n✅ Model uploaded successfully!")
    print(f"\n🌐 View at: https://huggingface.co/{repo_id}")
    
    print(f"\n📝 Next steps:")
    print(f"1. Update backend/main.py:")
    print(f"   MODEL_REPO = \"{repo_id}\"")
    print(f"\n2. Commit changes:")
    print(f"   git add backend/main.py")
    print(f"   git commit -m 'Use HF Hub for model loading'")
    print(f"   git push origin main")
    print(f"\n3. Cloud Run will download model at startup! 🚀")
    
except Exception as e:
    print(f"\n❌ Upload failed: {e}")
    sys.exit(1)
