import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
import joblib
from sklearn.ensemble import RandomForestClassifier

# Load the labeled dataset
df = pd.read_csv("data.csv")

# Step 1: Preprocess Labels
# Map sentiment labels to numeric values (e.g., "positive" -> 1, "neutral" -> 0, "negative" -> -1)
label_mapping = {"positive": 1, "neutral": 0, "negative": -1}
df['label'] = df['sentiment'].map(label_mapping)

# Step 2: Split Data
X = df['text']  # Feature: Text data
y = df['label']  # Target: Sentiment labels
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Step 3: Text Vectorization with TF-IDF
# Adjusted TF-IDF Vectorizer
tfidf = TfidfVectorizer(max_features=10000, ngram_range=(1, 2))
X_train_tfidf = tfidf.fit_transform(X_train)
X_test_tfidf = tfidf.transform(X_test)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train_tfidf, y_train)

# Evaluate
y_pred = model.predict(X_test_tfidf)
print("Classification Report:")
print(classification_report(y_test, y_pred))

# Save the Model and Vectorizer
joblib.dump(model, "models/random_forest.pkl")
joblib.dump(tfidf, "models/tfidf_vectorizer.pkl")
