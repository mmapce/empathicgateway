import joblib
import sys
import numpy as np
import backend.train_model

# Ensure BertEmbedder is available for pickle
sys.modules['__main__'].BertEmbedder = backend.train_model.BertEmbedder

print("Loading BERT model...")
model = joblib.load("backend/urgency_model.joblib")

test_phrases = [
    "my card is stolen",
    "i have been charged twice",
    "i am tired",
    "i am happy",
    "track my refund",
    "fraud detected",
    "are you kidding me",
    "this is ridiculous"
]

print("\n--- BERT Model Predictions ---")
for text in test_phrases:
    probs = model.predict_proba([text])[0]
    pred = model.predict([text])[0]
    max_prob = max(probs)
    print(f"Text: '{text}' -> Prediction: {pred} | Confidence: {max_prob:.4f} | Probs: {probs}")
