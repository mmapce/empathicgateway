import pandas as pd
from datasets import load_dataset

print("📥 Loading Dataset...")
dataset = load_dataset("bitext/Bitext-customer-support-llm-chatbot-training-dataset")
df = pd.DataFrame(dataset['train'])

print("\n--- Unique Intents ---")
unique_intents = df['intent'].unique()
for intent in sorted(unique_intents):
    print(intent)
