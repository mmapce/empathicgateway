
import joblib
import torch
from sklearn.base import BaseEstimator, TransformerMixin
from sentence_transformers import SentenceTransformer

# Define class again
class BertEmbedder(BaseEstimator, TransformerMixin):
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model_name = model_name
        self.model = None

    def fit(self, X, y=None):
        self.model = SentenceTransformer(self.model_name)
        return self

    def transform(self, X):
        if self.model is None:
             self.model = SentenceTransformer(self.model_name)
        if hasattr(X, 'tolist'): texts = X.tolist()
        else: texts = X
        return self.model.encode(texts, show_progress_bar=False)

try:
    model = joblib.load("backend/urgency_model.joblib")
    print("Model loaded successfully.")
    
    bert = model.named_steps['bert']
    print(f"Bert step model: {bert.model}")
    
    if bert.model is None:
        print("✅ SUCCESS: Bert model is None.")
    else:
        print(f"❌ FAILURE: Bert model is {type(bert.model)}")

except Exception as e:
    print(f"Error loading model: {e}")

import joblib
print(f"Joblib version: {joblib.__version__}")
