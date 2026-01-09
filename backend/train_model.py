import pandas as pd
import joblib
from datasets import load_dataset
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score
from sentence_transformers import SentenceTransformer
from sklearn.base import BaseEstimator, TransformerMixin

# Define BertEmbedder class at module level so it can be pickled/unpickled
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

def map_priority(intent):
    # CRITICAL: Money related, complaints
    if intent in ['payment_issue', 'get_refund', 'track_refund', 'complaint', 'check_cancellation_fee']:
        return 1
    # HIGH: Order changes, shipping, delivery
    elif intent in ['cancel_order', 'change_order', 'change_shipping_address', 'place_order', 'track_order', 'delivery_options', 'delivery_period']:
        return 2
    # NORMAL: Info, account, newsletter
    else:
        return 3

if __name__ == "__main__":
    # 1. Load Dataset
    print("📥 Loading Bitext Customer Support Dataset...")
    dataset = load_dataset("bitext/Bitext-customer-support-llm-chatbot-training-dataset")
    df = pd.DataFrame(dataset['train'])

    # 2. Feature Engineering: Map Intents to Priority
    print("🏷️  Mapping Intents to Priorities...")
    df['priority'] = df['intent'].apply(map_priority)

    # --- SYNTHETIC DATA INJECTION ---
    print("💉 Injecting Synthetic Critical Data...")
    synthetic_data = [
        {"instruction": "my card is stolen", "intent": "fraud_report", "priority": 1},
        {"instruction": "i have been charged twice", "intent": "payment_issue", "priority": 1},
        {"instruction": "fraud detected on my account", "intent": "fraud_report", "priority": 1},
        {"instruction": "unauthorized transaction report", "intent": "fraud_report", "priority": 1},
        {"instruction": "someone used my credit card", "intent": "fraud_report", "priority": 1},
        {"instruction": "double charge on my statement", "intent": "payment_issue", "priority": 1},
        {"instruction": "please refund duplicate payment", "intent": "payment_issue", "priority": 1},
        {"instruction": "urgent fraud alert", "intent": "fraud_report", "priority": 1},
        {"instruction": "my wallet was stolen", "intent": "fraud_report", "priority": 1},
        {"instruction": "block my account immediately", "intent": "fraud_report", "priority": 1},
        {"instruction": "i lost my wallet help", "intent": "fraud_report", "priority": 1},
        {"instruction": "lost wallet block card", "intent": "fraud_report", "priority": 1},
        {"instruction": "my wallet is lost and i dont remember my password", "intent": "fraud_report", "priority": 1}
    ]

    # Replicate to give weight
    synthetic_data = synthetic_data * 10 

    # --- SYNTHETIC NORMAL DATA INJECTION ---
    print("💉 Injecting Synthetic Normal Data...")
    synthetic_normal = [
        {"instruction": "i am tired", "intent": "chit_chat", "priority": 3},
        {"instruction": "hello", "intent": "greeting", "priority": 3},
        {"instruction": "hi there", "intent": "greeting", "priority": 3},
        {"instruction": "good morning", "intent": "greeting", "priority": 3},
        {"instruction": "have a nice day", "intent": "greeting", "priority": 3},
        {"instruction": "are you kidding me", "intent": "complaint", "priority": 3}, 
        {"instruction": "garbage text", "intent": "chit_chat", "priority": 3},
        # conversational / browsing overrides
        {"instruction": "just browsing thanks", "intent": "chit_chat", "priority": 3},
        {"instruction": "just browsing, thanks for the help", "intent": "chit_chat", "priority": 3},
        {"instruction": "i am just looking around", "intent": "chit_chat", "priority": 3},
        {"instruction": "no help needed just browsing", "intent": "chit_chat", "priority": 3},
        {"instruction": "checking prices thanks", "intent": "chit_chat", "priority": 3},
        {"instruction": "thanks for the help", "intent": "chit_chat", "priority": 3},
        {"instruction": "thank you", "intent": "chit_chat", "priority": 3},
        {"instruction": "thanks", "intent": "chit_chat", "priority": 3},
        {"instruction": "im ok", "intent": "chit_chat", "priority": 3}
    ]
    synthetic_normal = synthetic_normal * 10

    synthetic_df = pd.DataFrame(synthetic_data + synthetic_normal)
    df = pd.concat([df, synthetic_df], ignore_index=True)

    print("Distribution of Intents after Injection:")
    print(df['intent'].value_counts().head())

    # 3. Split Data
    X = df['instruction']
    y = df['intent'] # TRAIN ON INTENT NOW

    # 4. Build Pipeline
    print("⚙️  Training Model (BERT Embeddings + Logistic Regression)...")
    pipeline = Pipeline([
        ('bert', BertEmbedder()), 
        ('clf', LogisticRegression(max_iter=1000, class_weight='balanced', C=5.0)) 
    ])

    pipeline.fit(X, y)

    # 5. Evaluate
    y_pred = pipeline.predict(X)
    print("\n📊 Model Evaluation (Training Set):")
    print(f"Accuracy: {accuracy_score(y, y_pred):.4f}")
    print("\nClassification Report:")
    print(classification_report(y, y_pred))

    # 6. Save Model
    model_path = "backend/urgency_model.joblib"
    joblib.dump(pipeline, model_path)
    print(f"\n✅ Model saved to {model_path}")
