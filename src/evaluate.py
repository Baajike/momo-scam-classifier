"""
evaluate.py — quiz the model on the test set and report how it did.

THE FOUR OUTCOMES (a "confusion matrix" is just these four counts)
                          model says SCAM        model says LEGIT
    really SCAM           true positive (TP)     false negative (FN)  <- a scam got through
    really LEGIT          false positive (FP)    true negative (TN)
                          ^ a real message wrongly flagged

THE SCORES WE REPORT (all about the "scam" class)
    precision = TP / (TP + FP)
        "When the model shouts SCAM, how often is it right?"
        Low precision = annoying false alarms, people stop trusting it.

    recall    = TP / (TP + FN)
        "Of all the real scams, how many did it catch?"
        Low recall = scams slip through. For a safety tool, this hurts most.

    F1        = the balance of the two (their harmonic mean).
        One number that is only high when BOTH are high.

    accuracy  = (TP + TN) / everything
        We report it, but it can mislead: if 90% of messages are legit,
        a model that always says "legit" gets 90% accuracy and catches nothing.

WHY PER LANGUAGE?
An overall score can hide a model that works in English and fails in Twi.
Breaking results down by language is the most important part of this
project, because that is the actual research question.

Run:  python src/evaluate.py <model.joblib> <test.csv> <results_folder>
"""

import json
import sys
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")  # draw charts to files, no screen needed
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import (ConfusionMatrixDisplay, accuracy_score, confusion_matrix,
                             precision_recall_fscore_support)

POSITIVE = "scam"
MIN_RELIABLE = 30  # slices smaller than this are flagged as too small to trust


def scores(y_true, y_pred) -> dict:
    n_scam = int((y_true == POSITIVE).sum())
    n_flagged = int((y_pred == POSITIVE).sum())
    p, r, f, _ = precision_recall_fscore_support(
        y_true, y_pred, pos_label=POSITIVE, average="binary", zero_division=0)
    # If there are no real scams in a slice, recall and F1 cannot be measured.
    # If the model flagged nothing, precision cannot be measured.
    # Reporting 0.0 there would look like failure, so we report None ("n/a").
    return {
        "n": int(len(y_true)),
        "n_scam": n_scam,
        "precision": round(float(p), 3) if n_flagged else None,
        "recall": round(float(r), 3) if n_scam else None,
        "f1": round(float(f), 3) if n_scam else None,
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 3),
        "too_small_to_trust": bool(len(y_true) < MIN_RELIABLE),
    }


def main(model_path: str, test_path: str, out_dir: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    model = joblib.load(model_path)
    test = pd.read_csv(test_path, dtype=str, keep_default_na=False)
    test["predicted"] = model.predict(test["text"])
    test["scam_probability"] = model.predict_proba(test["text"])[:, list(model.classes_).index(POSITIVE)].round(3)

    # Overall, then one row per language
    results = {"overall": scores(test["label"], test["predicted"]), "by_language": {}}
    for lang, part in test.groupby("language"):
        results["by_language"][lang] = scores(part["label"], part["predicted"])

    # Scam types: recall only (did we catch each kind of scam?)
    scams = test[test["label"] == POSITIVE]
    results["recall_by_scam_type"] = {
        t: {"n": int(len(part)), "caught": int((part["predicted"] == POSITIVE).sum())}
        for t, part in scams.groupby("scam_type")
    }

    (out / "metrics.json").write_text(json.dumps(results, indent=2))

    # Confusion matrix picture
    labels = [POSITIVE, "legit"]
    cm = confusion_matrix(test["label"], test["predicted"], labels=labels)
    ConfusionMatrixDisplay(cm, display_labels=labels).plot(cmap="Blues", colorbar=False)
    plt.title("Baseline: confusion matrix (test set)")
    plt.tight_layout()
    plt.savefig(out / "confusion_matrix.png", dpi=150)
    plt.close()

    # Every mistake, so we can read them and understand WHY (error analysis)
    errors = test[test["label"] != test["predicted"]]
    errors[["id", "text", "label", "predicted", "scam_probability", "language", "scam_type"]] \
        .to_csv(out / "errors.csv", index=False)

    # Human-readable summary
    lines = ["# Evaluation results", "",
             f"Test set: {results['overall']['n']} messages ({results['overall']['n_scam']} scams)", "",
             "| Slice | n | Precision | Recall | F1 | Accuracy | Note |",
             "|---|---|---|---|---|---|---|"]
    def fmt(v):
        return "n/a" if v is None else v

    def row(name, s):
        note = "too few to trust" if s["too_small_to_trust"] else ""
        return (f"| {name} | {s['n']} | {fmt(s['precision'])} | {fmt(s['recall'])} | "
                f"{fmt(s['f1'])} | {s['accuracy']} | {note} |")
    lines.append(row("**Overall**", results["overall"]))
    for lang, s in results["by_language"].items():
        lines.append(row(lang, s))
    lines += ["", f"Mistakes: {len(errors)} (see errors.csv)"]
    (out / "report.md").write_text("\n".join(lines) + "\n")

    print("\n".join(lines))
    print(f"\nSaved metrics.json, report.md, confusion_matrix.png, errors.csv -> {out}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit("Usage: python src/evaluate.py <model.joblib> <test.csv> <results_folder>")
    main(sys.argv[1], sys.argv[2], sys.argv[3])
