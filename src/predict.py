"""
predict.py — use the trained model on any message you type.

This is what the project is FOR: you give it a message, it tells you
whether it looks like a scam, how sure it is, and which words made it
decide that.

Run:  python src/predict.py models/baseline.joblib
Then type or paste a message and press Enter. Type q to quit.
"""

import sys
from pathlib import Path

import joblib

sys.path.insert(0, str(Path(__file__).resolve().parent))
from anonymise import anonymise_text  # noqa: E402

POSITIVE = "scam"


def explain(model, text: str, n: int = 5) -> list[tuple[str, float]]:
    """Return the features in THIS message that pushed hardest toward 'scam'."""
    features = model.named_steps["features"]
    weights = model.named_steps["classifier"].coef_[0]
    names = features.get_feature_names_out()
    row = features.transform([text]).tocoo()
    contributions = [(names[j], value * weights[j]) for j, value in zip(row.col, row.data)]
    # Show only whole-word features: letter chunks are hard for people to read
    words = [(name.replace("words__", ""), c) for name, c in contributions if name.startswith("words__")]
    return sorted(words, key=lambda x: x[1], reverse=True)[:n]


def main(model_path: str) -> None:
    model = joblib.load(model_path)
    scam_col = list(model.classes_).index(POSITIVE)
    print("Paste a message and press Enter (q to quit).\n")

    while True:
        message = input("> ").strip()
        if message.lower() in {"q", "quit", "exit"}:
            break
        if not message:
            continue

        clean = anonymise_text(message)          # same cleaning as training
        prob = model.predict_proba([clean])[0][scam_col]
        verdict = "LIKELY SCAM" if prob >= 0.5 else "probably legit"

        print(f"  {verdict}  (scam probability: {prob:.0%})")
        reasons = [f"{w!r}" for w, c in explain(model, clean) if c > 0]
        if reasons:
            print(f"  Words that raised suspicion: {', '.join(reasons)}")
        print()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python src/predict.py <model.joblib>")
    main(sys.argv[1])
