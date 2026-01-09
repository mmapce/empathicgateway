
import joblib
import torch
import sys
import os

print(f"Python: {sys.version}")
print(f"Joblib: {joblib.__version__}")
print(f"Torch: {torch.__version__}")

# Add valid path if needed
sys.path.append("/app")

try:
    import backend.train_model
    # Patch main for pickle compatibility if needed
    sys.modules['__main__'].BertEmbedder = backend.train_model.BertEmbedder
    print("Imported backend.train_model successfully")
except ImportError as e:
    print(f"ImportError: {e}")
    # Try importing from current dir?
    try:
        from backend import train_model
        sys.modules['__main__'].BertEmbedder = train_model.BertEmbedder
        print("Imported from local dir")
    except Exception as e2:
        print(f"Fallback import failed: {e2}")

model_path = "/app/backend/urgency_model.joblib"
if not os.path.exists(model_path):
    print(f"File not found: {model_path}")
    sys.exit(1)

print(f"Loading {model_path}...")
try:
    model = joblib.load(model_path)
    print("✅ SUCCESS: Model loaded!")
    if hasattr(model, 'named_steps'):
        print(f"Bert step: {model.named_steps['bert'].model}")
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
