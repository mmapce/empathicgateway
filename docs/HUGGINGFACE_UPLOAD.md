# Upload Model to Hugging Face Hub

This guide explains how to upload your trained model to Hugging Face Hub for runtime loading.

## Prerequisites

```bash
pip install huggingface_hub
```

## Steps

### 1. Create Hugging Face Account

1. Go to https://huggingface.co/join
2. Create an account
3. Generate an access token at https://huggingface.co/settings/tokens

### 2. Login to Hugging Face CLI

```bash
huggingface-cli login
```

Enter your access token when prompted.

### 3. Create a New Model Repository

```bash
huggingface-cli repo create empathicgateway-intent-classifier --type model
```

### 4. Upload the Model

```python
from huggingface_hub import HfApi

api = HfApi()

# Upload model file
api.upload_file(
    path_or_fileobj="backend/urgency_model.joblib",
    path_in_repo="urgency_model.joblib",
    repo_id="YOUR_USERNAME/empathicgateway-intent-classifier",
    repo_type="model"
)

print("✅ Model uploaded successfully!")
```

### 5. Update Backend Configuration

In `backend/main.py`, update the `MODEL_REPO` variable:

```python
MODEL_REPO = "YOUR_USERNAME/empathicgateway-intent-classifier"
```

### 6. Test Locally

```bash
python -c "from huggingface_hub import hf_hub_download; print(hf_hub_download(repo_id='YOUR_USERNAME/empathicgateway-intent-classifier', filename='urgency_model.joblib'))"
```

## Alternative: Use Python Script

Create `upload_model.py`:

```python
#!/usr/bin/env python3
from huggingface_hub import HfApi, create_repo
import os

# Configuration
USERNAME = "YOUR_USERNAME"  # Replace with your HF username
REPO_NAME = "empathicgateway-intent-classifier"
MODEL_PATH = "backend/urgency_model.joblib"

# Initialize API
api = HfApi()

# Create repository (if it doesn't exist)
try:
    repo_id = f"{USERNAME}/{REPO_NAME}"
    create_repo(repo_id, repo_type="model", exist_ok=True)
    print(f"✅ Repository created: {repo_id}")
except Exception as e:
    print(f"Repository might already exist: {e}")

# Upload model
print(f"📤 Uploading {MODEL_PATH}...")
api.upload_file(
    path_or_fileobj=MODEL_PATH,
    path_in_repo="urgency_model.joblib",
    repo_id=repo_id,
    repo_type="model"
)

print(f"✅ Model uploaded to: https://huggingface.co/{repo_id}")
```

Run it:

```bash
python upload_model.py
```

## Benefits

- ✅ Smaller Docker images (no 87MB model file)
- ✅ Faster Cloud Run deployments
- ✅ Model versioning via HF Hub
- ✅ Easy model updates without redeploying
- ✅ Automatic caching on Cloud Run

## Notes

- Model is cached in `/tmp/model_cache` on Cloud Run
- First request will be slower (model download)
- Subsequent requests use cached model
- Fallback to local model if HF download fails
