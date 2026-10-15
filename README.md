# MoMo Scam Classifier

Detecting mobile money scam messages in **English, Ghanaian Pidgin, Twi, and code-mixed text**.

> Status: work in progress. The pipeline runs end to end. The real dataset is being collected.

## The problem

In Ghana, most reported scams try to get Mobile Money payments or MoMo account access. Scammers usually reach people through SMS and WhatsApp. They write in English, Pidgin, Twi, or a mix of all three.

Most published scam detectors are trained on English messages from Europe and North America. Some African work exists for Swahili and Chichewa, but I could not find a public dataset of Ghanaian scam messages in Twi or Pidgin.

This project asks one question:

**How well can a text classifier detect MoMo scam messages written the way Ghanaians actually write, and where does it fail?**

## What this repo contains

| Folder | What is inside |
|---|---|
| `docs/LABELLING_GUIDE.md` | The rules for deciding whether a message is a scam, and how to tag its language |
| `docs/LEARNING_NOTES.md` | Plain-language explanations of every concept used here |
| `data/practice/` | A small **made-up** practice set, only for testing that the code runs. Never used for results. |
| `data/raw/` | Real collected messages (not committed to GitHub, for privacy) |
| `src/anonymise.py` | Removes phone numbers, transaction IDs, and other personal details |
| `src/split.py` | Splits data into training and test sets without letting copied scam templates leak across |
| `src/train_baseline.py` | Trains the baseline model (TF-IDF + logistic regression) |
| `src/evaluate.py` | Scores the model overall and separately for each language |
| `tests/` | Automated checks for the anonymiser and splitter |

## How to run it

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 1. Remove personal details
python src/anonymise.py data/practice/practice_messages.csv data/processed/clean.csv

# 2. Split into train and test (duplicate-aware)
python src/split.py data/processed/clean.csv data/processed

# 3. Train the baseline model
python src/train_baseline.py data/processed/train.csv models/baseline.joblib

# 4. Evaluate on the test set
python src/evaluate.py models/baseline.joblib data/processed/test.csv results/baseline

# Run the automated tests
python -m pytest tests
```

To use real data, put your collected CSV in `data/raw/` and point step 1 at it.

## Roadmap

- [x] Labelling guide and data format
- [x] Anonymiser
- [x] Duplicate-aware train/test split
- [x] Baseline model (TF-IDF + logistic regression)
- [x] Per-language evaluation
- [ ] Collect and label real messages
- [ ] Second annotator on a subset and agreement score (Cohen's kappa)
- [ ] Fine-tune a multilingual African language model
- [ ] Error analysis and written report

## Related work

- Mambina, Ndibwile and Michael (2022), *Classifying Swahili Smishing Attacks for Mobile Money Users*, IEEE Access.
- *Using Machine Learning to Detect Fraudulent SMSs in Chichewa* (2025), arXiv:2502.16947.
- BongoScam: a public Swahili SMS scam dataset on Kaggle.
- ExAIS SMS Spam Dataset: Nigerian SMS spam collected at FUNAAB.

## Ethics and privacy

Every real message is collected with the owner's permission. Phone numbers, names, and transaction IDs are removed before anything is stored. Raw data is never committed to this repository.

## Author

Immanuella Baajike
