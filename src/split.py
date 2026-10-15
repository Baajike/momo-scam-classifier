"""
split.py — divide the data into a TRAINING set and a TEST set, fairly.

THE IDEA IN ONE SENTENCE
The model studies the training set, then we quiz it on the test set,
which it has never seen. That quiz score is our honest estimate of how
well it works on new messages.

THE TRAP THIS FILE AVOIDS (template leakage)
Scammers send the same message thousands of times, changing only the
amount or the phone number:

    "I mistakenly send GHS 200 to your number, send it back to 024..."
    "I mistakenly send GHS 500 to your number, send it back to 055..."

If one copy lands in training and the other in the test set, the model
has effectively seen the test question in advance. The score looks
amazing, but it is fake. Many published papers report 99% for this
reason.

So before splitting, we group near-identical messages together, and a
whole group always goes to the same side (all training, or all test).

HOW WE FIND NEAR-COPIES
1. Normalise each message: lowercase, turn every digit into 0, remove
   punctuation. Now "GHS 200" and "GHS 500" both become "ghs 000".
2. Turn each message into a list of 3-to-5-letter chunks and compare
   messages by how many chunks they share (cosine similarity, 0 to 1).
3. Any two messages more similar than SIMILARITY_THRESHOLD are linked,
   and linked messages form one group.

Run:  python src/split.py <clean.csv> <output_folder>
"""

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse.csgraph import connected_components
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import StratifiedGroupKFold

SIMILARITY_THRESHOLD = 0.8   # how alike two messages must be to count as copies
TEST_FRACTION_FOLDS = 5      # 5 folds -> about 1/5 (20%) of the data goes to test
RANDOM_SEED = 42             # fixes the "random" shuffle so results are repeatable


def normalise(text: str) -> str:
    """Make near-copies look identical: lowercase, digits -> 0, no punctuation."""
    text = text.lower()
    text = re.sub(r"<[a-z_]+>", " ", text)    # drop placeholder tags like <PHONE>
    text = re.sub(r"\d", "0", text)
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def find_template_groups(texts: list[str]) -> np.ndarray:
    """Give every message a group number. Near-copies share a number."""
    normalised = [normalise(t) for t in texts]
    vectoriser = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5))
    X = vectoriser.fit_transform(normalised)

    # X rows are length-1 vectors, so X @ X.T gives cosine similarity for every pair
    similarity = (X @ X.T).tocsr()
    similarity.data[similarity.data < SIMILARITY_THRESHOLD] = 0
    similarity.eliminate_zeros()

    # Messages linked directly or through a chain of links end up in one group
    _, group_ids = connected_components(similarity, directed=False)
    return group_ids


def main(in_path: str, out_dir: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(in_path, dtype=str, keep_default_na=False)
    total = len(df)

    # 'unsure' rows cannot teach or test the model, so we set them aside and count them
    unsure = int((df["label"] == "unsure").sum())
    df = df[df["label"].isin(["scam", "legit"])].reset_index(drop=True)

    df["template_group"] = find_template_groups(df["text"].tolist())

    # Stratify on label + language so the test set gets a fair share of each
    # language and each class, while groups stay whole.
    strata = df["label"] + "_" + df["language"]
    splitter = StratifiedGroupKFold(n_splits=TEST_FRACTION_FOLDS, shuffle=True, random_state=RANDOM_SEED)
    train_idx, test_idx = next(splitter.split(df, strata, groups=df["template_group"]))

    train, test = df.iloc[train_idx], df.iloc[test_idx]

    # Safety check: no group may appear on both sides
    leaked = set(train["template_group"]) & set(test["template_group"])
    assert not leaked, f"Template groups leaked across the split: {leaked}"

    train.to_csv(out / "train.csv", index=False)
    test.to_csv(out / "test.csv", index=False)

    group_sizes = df["template_group"].value_counts()
    report = {
        "total_rows": total,
        "unsure_set_aside": unsure,
        "used_rows": len(df),
        "template_groups": int(df["template_group"].nunique()),
        "largest_group_size": int(group_sizes.max()),
        "rows_in_groups_of_2_or_more": int(group_sizes[group_sizes > 1].sum()),
        "train_rows": len(train),
        "test_rows": len(test),
        "train_counts": train.groupby(["language", "label"]).size().unstack(fill_value=0).to_dict(),
        "test_counts": test.groupby(["language", "label"]).size().unstack(fill_value=0).to_dict(),
    }
    (out / "split_report.json").write_text(json.dumps(report, indent=2))

    print(f"{total} rows in, {unsure} 'unsure' set aside.")
    print(f"Found {report['template_groups']} template groups "
          f"({report['rows_in_groups_of_2_or_more']} rows are near-copies of something else).")
    print(f"Train: {len(train)} rows | Test: {len(test)} rows | No template leaks across the split.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: python src/split.py <clean.csv> <output_folder>")
    main(sys.argv[1], sys.argv[2])
