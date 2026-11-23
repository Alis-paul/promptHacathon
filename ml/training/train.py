import argparse
import os
import sys
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
)
import joblib
import json
from datetime import datetime

# Allowed canonical department labels
ALLOWED_LABELS = [
    "Roads",
    "Water Supply",
    "Drainage",
    "Sanitation",
    "Electrical / Streetlights",
]

def validate_dataset(df: pd.DataFrame):
    # Check required columns
    if "text" not in df.columns or "department" not in df.columns:
        raise ValueError("Dataset must contain 'text' and 'department' columns.")
    # Drop rows with missing values
    df = df.dropna(subset=["text", "department"]).copy()
    # Strip whitespace
    df["text"] = df["text"].astype(str).str.strip()
    df["department"] = df["department"].astype(str).str.strip()
    # Remove empty texts
    df = df[df["text"] != ""]
    # Validate labels
    invalid_labels = set(df["department"]).difference(ALLOWED_LABELS)
    if invalid_labels:
        raise ValueError(f"Invalid department labels found: {invalid_labels}")
    # Ensure at least one sample per class
    class_counts = df["department"].value_counts()
    missing = [label for label in ALLOWED_LABELS if label not in class_counts]
    if missing:
        raise ValueError(f"Missing samples for departments: {missing}")
    return df

def build_pipeline():
    tfidf = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=1,
        token_pattern=r"(?u)\b\w+\b",
    )
    clf = LogisticRegression(max_iter=1000, class_weight="balanced")
    pipeline = Pipeline([("tfidf", tfidf), ("clf", clf)])
    return pipeline

def train_and_evaluate(data_path: str, model_dir: str, random_state: int = 42):
    df = pd.read_csv(data_path)
    df = validate_dataset(df)
    X = df["text"].values
    y = df["department"].values
    # Split with stratification if possible
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.3, random_state=random_state, stratify=y
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=random_state, stratify=y_temp
    )
    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    # Evaluation helper
    def eval_split(name, X_split, y_split):
        preds = pipeline.predict(X_split)
        probs = pipeline.predict_proba(X_split)
        acc = accuracy_score(y_split, preds)
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_split, preds, average="macro", zero_division=0
        )
        per_class = precision_recall_fscore_support(
            y_split, preds, labels=ALLOWED_LABELS, zero_division=0
        )
        cm = confusion_matrix(y_split, preds, labels=ALLOWED_LABELS)
        return {
            "accuracy": acc,
            "macro_precision": precision,
            "macro_recall": recall,
            "macro_f1": f1,
            "per_class": {
                label: {
                    "precision": p,
                    "recall": r,
                    "f1": f,
                }
                for label, p, r, f in zip(ALLOWED_LABELS, *per_class)
            },
            "confusion_matrix": cm.tolist(),
        }

    metrics = {
        "train": eval_split("train", X_train, y_train),
        "validation": eval_split("validation", X_val, y_val),
        "test": eval_split("test", X_test, y_test),
    }

    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "complaint_classifier.joblib")
    joblib.dump(pipeline, model_path)
    metadata = {
        "model_version": "1.0",
        "trained_at": datetime.utcnow().isoformat() + "Z",
        "labels": ALLOWED_LABELS,
        "metrics": metrics,
        "data_path": os.path.abspath(data_path),
    }
    metadata_path = os.path.join(model_dir, "metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Model saved to {model_path}")
    print(f"Metadata saved to {metadata_path}")
    return model_path, metadata_path

def main():
    parser = argparse.ArgumentParser(description="Train complaint classification model")
    parser.add_argument("--data", required=True, help="Path to CSV training data (must have 'text','department' columns)")
    parser.add_argument(
        "--model-dir",
        default=os.path.join(os.getcwd(), "ml", "models"),
        help="Directory to save model artifact and metadata",
    )
    args = parser.parse_args()
    train_and_evaluate(args.data, args.model_dir)

if __name__ == "__main__":
    main()
