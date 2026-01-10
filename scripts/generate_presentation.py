import json
import os

OUTPUT_FILE = "docs/EmpathicGateway_Interactive_Demo.ipynb"

# Notebook Structure
notebook = {
    "cells": [],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "codemirror_mode": {"name": "ipython", "version": 3},
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.8.5",
        },
    },
    "nbformat": 4,
    "nbformat_minor": 4,
}


def add_markdown(content):
    notebook["cells"].append(
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [line + "\n" for line in content.split("\n")],
        }
    )


def add_code(code):
    notebook["cells"].append(
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [line + "\n" for line in code.split("\n")],
        }
    )


# --- NOTEBOOK CONTENT ---

# 1. Header
add_markdown("""# 🚀 EmpathicGateway: Interactive Backend Demo
### _Run the AI Brain of the system right here!_

This notebook allows you to execute the core logic of the EmpathicGateway backend. You will:
1.  **Initialize** the AI models.
2.  **Train** a fresh intent classifier on synthetic data.
3.  **Run Inference** on your own text to see Priority and PII masking in action.

---
### 🛠️ Step 1: Install Dependencies
Run this cell to ensure you have the required libraries.
""")

add_code(
    """!pip install sentence-transformers scikit-learn pandas joblib transformers numpy"""
)

# 2. Imports & Definitions
add_markdown("""### 🧠 Step 2: Define The AI Architecture
Here we define the `BertEmbedder` class, which connects our lightweight Logistic Regression to the powerful BERT Language Model.
""")

add_code("""import pandas as pd
import numpy as np
import re
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin
from sentence_transformers import SentenceTransformer

# This is the exact class from backend/train_model.py
class BertEmbedder(BaseEstimator, TransformerMixin):
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model_name = model_name
        self.model = None

    def fit(self, X, y=None):
        print(f"📥 Loading BERT ({self.model_name})...")
        self.model = SentenceTransformer(self.model_name)
        return self

    def transform(self, X):
        if self.model is None:
             self.model = SentenceTransformer(self.model_name)
        
        # Handle inputs
        if hasattr(X, 'tolist'): texts = X.tolist()
        else: texts = X
            
        return self.model.encode(texts, show_progress_bar=False)

def map_priority(intent):
    if intent in ['payment_issue', 'fraud_report', 'stolen_card']: return 1  # CRITICAL
    elif intent in ['track_order', 'cancel_order']: return 2                 # HIGH
    else: return 3                                                           # NORMAL

print("✅ Architecture Defined!")
""")

# 3. Data & Training
add_markdown("""### 🎓 Step 3: Train the Model (Live!)
We will use the **Synthetic Dataset** strategy directly in this notebook. Notice how we explicitly teach the model about "Just Browsing" vs "Fraud".
""")

add_code("""# 1. Create Training Data
data = [
    # --- CRITICAL (Priority 1) ---
    {"text": "my wallet was stolen", "intent": "fraud_report"},
    {"text": "someone used my credit card", "intent": "fraud_report"},
    {"text": "unauthorized charge on my account", "intent": "payment_issue"},
    {"text": "i need to block my card immediately", "intent": "stolen_card"},
    
    # --- HIGH (Priority 2) ---
    {"text": "where is my order", "intent": "track_order"},
    {"text": "cancel my order please", "intent": "cancel_order"},
    {"text": "change my shipping address", "intent": "track_order"},
    
    # --- NORMAL (Priority 3) ---
    {"text": "hello", "intent": "greeting"},
    {"text": "just browsing thanks", "intent": "chit_chat"},
    {"text": "i am just looking around", "intent": "chit_chat"},
    {"text": "thank you for the help", "intent": "chit_chat"},
    {"text": "do you have this in blue", "intent": "product_question"}
]

# Multiply data to mimic real training volume
df = pd.DataFrame(data * 5)
df['priority'] = df['intent'].apply(map_priority)

print(f"📚 Dataset Created: {len(df)} samples")
print(df.head())

# 2. Build Pipeline
pipeline = Pipeline([
    ('embedding', BertEmbedder(model_name='all-MiniLM-L6-v2')),
    ('classifier', LogisticRegression(C=1.0, max_iter=500))
])

# 3. Train
print("\\n⚙️ Training Model... (This uses CPU, might take 10-20s)")
pipeline.fit(df['text'], df['intent'])
print("✅ Model Trained Successfully!")
""")

# 4. PII Masking
add_markdown("""### 🛡️ Step 4: PII Masking Logic
The backend creates a "Safe Text" version of every request. Here is the logic:
""")

add_code("""def mask_pii(text):
    safe_text = text
    detected_types = []
    
    # 1. Email Regex
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    if re.search(email_pattern, safe_text):
        safe_text = re.sub(email_pattern, '[EMAIL]', safe_text)
        detected_types.append("EMAIL")
        
    # 2. Credit Card Regex (Simple 16 digits)
    cc_pattern = r'(?:\d[ -]*?){13,16}'
    # Avoid false positives with simple check
    matches = re.findall(cc_pattern, safe_text)
    for m in matches:
        if len(re.sub(r'\D', '', m)) >= 13:
            safe_text = safe_text.replace(m, '[CREDIT_CARD]')
            if "CREDIT_CARD" not in detected_types: detected_types.append("CREDIT_CARD")
            
    return safe_text, detected_types

print("✅ PII System Ready.")
""")

# 5. Interactive Demo
add_markdown("""### 🎮 Step 5: Interactive Demo
**Try it yourself!** Change the `text` variable below and run the cell.
""")

add_code("""# --- INPUT YOUR TEXT HERE ---
user_input = "I lost my wallet and my email is murat@test.com"
# ----------------------------

# 1. Safety First (PII)
safe_input, pii = mask_pii(user_input)

# 2. Model Prediction
prediction = pipeline.predict([safe_input])[0]
probs = pipeline.predict_proba([safe_input])[0]
confidence = max(probs)
priority = map_priority(prediction)

# 3. Visualization
priority_map = {1: "🔴 CRITICAL", 2: "🟠 HIGH", 3: "🟢 NORMAL"}
priority_label = priority_map.get(priority, "UNKNOWN")

print(f"📝 Original: '{user_input}'")
print(f"🛡️ Masked:   '{safe_input}'")
print("-" * 30)
print(f"🧠 Intent:   {prediction.upper()}")
print(f"🚦 Priority: {priority_label}")
print(f"📊 Conf:     {confidence:.1%}")

if pii:
    print(f"⚠️ PII Detected: {pii}")
""")

# 6. Just Browsing Test
add_markdown("""### 🧪 Validation: The "Just Browsing" Test
Let's verify our specific fix for the 'Just browsing' edge case.
""")

add_code("""test_cases = [
    "Just browsing, thanks!",
    "I need a refund immediately",
    "Hello there",
    "Where is my stuff?"
]

print(f"{'INPUT':<30} | {'INTENT':<15} | {'PRIORITY'}")
print("-" * 60)

for text in test_cases:
    pred = pipeline.predict([text])[0]
    prio = map_priority(pred)
    label = {1:"CRITICAL", 2:"HIGH", 3:"NORMAL"}[prio]
    print(f"{text:<30} | {pred:<15} | {label}")
""")

# Save File
with open(OUTPUT_FILE, "w") as f:
    json.dump(notebook, f, indent=2)

print(f"Interactive Notebook created at {OUTPUT_FILE}")
