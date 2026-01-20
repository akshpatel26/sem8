# train_ml_model.py
import json
import pickle
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

# Load database
db_path = Path("ml_models/content_db.json")
with open(db_path, 'r') as f:
    db = json.load(f)

# Prepare training data
texts = []
labels = []

for sem, subjects in db.items():
    for subject, data in subjects.items():
        # Combine topics as text
        text = " ".join(data['topics'])
        texts.append(text)
        labels.append(subject)

# Train TF-IDF
vectorizer = TfidfVectorizer(max_features=100)
X = vectorizer.fit_transform(texts)

# Train classifier
classifier = MultinomialNB()
classifier.fit(X, labels)

# Save models
pickle.dump(vectorizer, open("ml_models/tfidf_vectorizer.pkl", "wb"))
pickle.dump(classifier, open("ml_models/subject_classifier.pkl", "wb"))

print("✅ ML Models trained and saved!")