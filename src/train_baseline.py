"""
train_baseline.py — train our first, simple model.

WHAT IS A "BASELINE"?
The simplest reasonable model. Later, fancier models must beat it.
If a big neural network only scores 1% higher than this, that is worth
knowing, and saying, in the report.

HOW THIS MODEL WORKS (two steps, joined in a "pipeline")

Step 1 — TF-IDF: turn text into numbers.
    Computers cannot read words, only numbers. TF-IDF gives every word
    (and every short letter chunk) a score in each message:
      - higher if it appears often in THIS message   (TF, term frequency)
      - lower if it appears in almost EVERY message  (IDF, inverse document frequency)
    So "the" gets a tiny score, while "mistakenly" or "reverse" gets a big one.

    We do this twice and join the results:
      - word features:   single words and pairs ("send back")
      - letter features: 2-5 letter chunks ("mista", "abeg")
    Letter chunks matter for us because Pidgin and Twi spelling varies a
    lot ("abeg", "abeeg", "a beg"). Chunks still match when spelling wobbles.

Step 2 — Logistic regression: learn a weight for every feature.
    Each feature gets a weight. Positive pushes toward "scam", negative
    toward "legit". The model adds up (feature score x weight) for a
    message and turns the total into a probability between 0 and 1.
    Training means finding the weights that best match our labels.

    class_weight="balanced" tells it to care equally about both classes,
    even if we have more legit messages than scams.

Run:  python src/train_baseline.py <train.csv> <model_output.joblib>
"""

import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline


def build_model() -> Pipeline:
    features = FeatureUnion([
        ("words", TfidfVectorizer(analyzer="word", ngram_range=(1, 2), lowercase=True, min_df=1)),
        ("chars", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), lowercase=True, min_df=1)),
    ])
    classifier = LogisticRegression(class_weight="balanced", max_iter=2000, random_state=42)
    return Pipeline([("features", features), ("classifier", classifier)])


def show_top_features(model: Pipeline, n: int = 15) -> None:
    """Print the features the model leans on most. This is how we 'see inside' it."""
    names = model.named_steps["features"].get_feature_names_out()
    weights = model.named_steps["classifier"].coef_[0]
    positive_class = model.named_steps["classifier"].classes_[1]
    order = np.argsort(weights)

    print(f"\nTop {n} features pushing toward '{positive_class}':")
    for i in order[::-1][:n]:
        print(f"  {weights[i]:+.2f}  {names[i]!r}")
    print(f"\nTop {n} features pushing away from '{positive_class}':")
    for i in order[:n]:
        print(f"  {weights[i]:+.2f}  {names[i]!r}")


def main(train_path: str, model_path: str) -> None:
    train = pd.read_csv(train_path, dtype=str, keep_default_na=False)
    X, y = train["text"], train["label"]

    print(f"Training on {len(train)} messages: {y.value_counts().to_dict()}")
    model = build_model()
    model.fit(X, y)

    joblib.dump(model, model_path)
    print(f"Saved model -> {model_path}")
    show_top_features(model)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: python src/train_baseline.py <train.csv> <model_output.joblib>")
    main(sys.argv[1], sys.argv[2])
