
import joblib
import torch
import os
from sklearn.base import BaseEstimator, TransformerMixin
from sentence_transformers import SentenceTransformer

# Define BertEmbedder class so joblib can find it
class BertEmbedder(BaseEstimator, TransformerMixin):
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model_name = model_name
        self.model = None

    def fit(self, X, y=None):
        print("📥 Loading BERT Model for Embedding...")
        self.model = SentenceTransformer(self.model_name)
        return self

    def transform(self, X):
        # logging.info("🧠 Generating BERT Embeddings...")
        if self.model is None:
             self.model = SentenceTransformer(self.model_name)
        
        # Handle different input types (Pandas Series vs List)
        if hasattr(X, 'tolist'):
            texts = X.tolist()
        else:
            texts = X
            
        return self.model.encode(texts, show_progress_bar=False)

model_path = "backend/urgency_model.joblib"
output_path = "backend/urgency_model.joblib" # Overwrite? Or new name? Let's overwrite to keep deployment simple.

print(f"Loading {model_path}...")
try:
    # Attempt to load. If it fails here on Mac, it's weird because Mac has MPS.
    model = joblib.load(model_path)
    print("Model loaded.")
    
    # Check if it has a 'device' attribute or similar, or try to move it.
    # If it's a sklearn pipeline, we iterate steps.
    if hasattr(model, 'steps'):
        print("Model is a Pipeline.")
        for name, step in model.steps:
            print(f"Checking step: {name}")
            if hasattr(step, 'model'):
                print(f"Refusing to save {name} internal model state (setting to None to force reload)")
                # This avoids saving device-specific tensors (MPS/CUDA) since the model is pre-trained and not fine-tuned.
                step.model = None
                
    elif hasattr(model, 'model'):
         step.model = None
    
    print(f"Saving to {output_path}...")
    joblib.dump(model, output_path)
    print("Done.")

except Exception as e:
    print(f"Error: {e}")
