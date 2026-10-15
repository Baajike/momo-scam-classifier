# Learning Notes

Everything in this project, explained from zero. Read it in order. Each section builds on the one before.

---

## 1. What is machine learning?

Normal programming: **you** write the rules.

```
if "send it back" in message and "mistake" in message:
    say "scam"
```

That breaks fast. Scammers change one word and your rule misses it. And you would need thousands of rules for English, Pidgin, and Twi.

Machine learning flips it: you give the computer **examples with the right answers**, and it works out the rules itself.

```
"I mistakenly send GHS 200, send it back"   -> scam
"Are we still meeting at 4pm?"              -> legit
... 1,000 more examples ...
```

The computer studies the examples and builds its own internal rules. Then it can judge messages it has never seen.

**The examples are called the dataset. The right answers are called labels.** That is why the labelling guide matters so much: the model can only be as good as our labels.

---

## 2. What kind of problem is this?

It is **text classification**: put a piece of text into one of a fixed set of boxes. We have two boxes, `scam` and `legit`, so it is **binary** classification.

It is also **supervised** learning, because we supervise the computer with correct answers. (Unsupervised learning is when there are no labels and the computer just finds patterns on its own.)

The branch of AI that deals with human language is called **NLP: Natural Language Processing**. This project is an NLP project, which is the department at MBZUAI it fits.

---

## 3. Step by step: what the pipeline does

A **pipeline** is a chain of steps where each step's output feeds the next one. Ours has four:

```
raw messages
   │  anonymise.py   remove phone numbers, names, IDs
   ▼
clean messages
   │  split.py       divide into training set and test set
   ▼
train.csv + test.csv
   │  train_baseline.py   model learns from train.csv
   ▼
saved model
   │  evaluate.py    quiz the model on test.csv
   ▼
scores, confusion matrix, list of mistakes
```

---

## 4. Anonymising (anonymise.py)

Real messages contain real people's phone numbers and names. We replace them with tags:

```
"send it back to 0244123456"  ->  "send it back to <PHONE>"
```

Two reasons:
1. **Privacy.** We must not store or publish people's personal data. Ghana has a Data Protection Act.
2. **It helps the model.** The model should learn "scams often contain a phone number to send money to", not memorise one specific scammer's number. The tag `<PHONE>` teaches the general pattern.

The anonymiser uses **regular expressions (regex)**: patterns that describe text. For example `\d{8,}` means "8 or more digits in a row".

---

## 5. Training set and test set (split.py)

Imagine a teacher who gives students the exact exam questions to practise. Everyone scores 100%, but that tells you nothing about whether they understand.

Same with models. So we split the data:
- **Training set (about 80%)**: the model studies these.
- **Test set (about 20%)**: hidden during training. We use it once, at the end, to see how well the model handles messages it has never seen.

The test score is our honest estimate of real-world performance.

### The leakage trap

Scammers send the same message thousands of times, changing only the amount:

```
"I mistakenly send GHS 200 to your number, send it back"
"I mistakenly send GHS 500 to your number, send it back"
```

If one copy is in training and the other is in the test set, the model has basically seen the exam question. The score looks amazing but is fake. This is called **data leakage**, and many published scam-detection papers report 99% accuracy partly because of it.

`split.py` fixes this by finding near-copies first and keeping each group on one side of the split. **This is a strong point to mention in an interview.** It shows you understand why results can lie.

How it finds near-copies:
1. **Normalise**: lowercase everything, turn every digit into 0. Now "GHS 200" and "GHS 500" are identical.
2. **Compare**: break each message into short letter chunks and measure how many chunks two messages share. This is called **cosine similarity**, a score from 0 (nothing in common) to 1 (identical).
3. **Group**: any two messages scoring above 0.8 go in the same group.

It also **stratifies**: it makes sure the test set gets a fair share of each language and each label, so we do not end up with a test set that has zero Twi scams.

---

## 6. Turning text into numbers: TF-IDF

Computers only do maths on numbers. So every message must become a list of numbers. The method we use is **TF-IDF**.

- **TF (term frequency)**: how often a word appears in this message.
- **IDF (inverse document frequency)**: how rare the word is across all messages.

Multiply them. A word gets a **high** score if it is common in this message but rare overall.

| Word | Appears in... | TF-IDF score |
|---|---|---|
| "the" | almost every message | very low (it tells us nothing) |
| "mistakenly" | a few messages | high (it is distinctive) |

Each message becomes a long list of scores, one per word in our vocabulary. These numbers are called **features**.

We make two kinds of features:
- **Word features**: whole words and two-word pairs ("send back").
- **Letter-chunk features**: 2 to 5 letters ("abeg", "mista").

Letter chunks matter for Pidgin and Twi, where there is no fixed spelling. "abeg", "abeeg", and "a beg" share chunks, so the model still recognises them.

---

## 7. The model: logistic regression

Once a message is a list of numbers, the model gives every feature a **weight**:
- positive weight: pushes toward "scam"
- negative weight: pushes toward "legit"

For a new message, it multiplies each feature score by its weight, adds everything up, and turns the total into a **probability** between 0 and 1. Above 0.5 means "scam".

**Training** = finding the weights that make the model's answers match our labels as closely as possible.

Why start with this simple model?
- It trains in seconds on a laptop.
- **You can look inside it.** `train_baseline.py` prints the features with the biggest weights. You can say exactly why it called something a scam. Big neural networks are much harder to explain.
- It is the **baseline**: the score any fancier model must beat. If a huge model only beats it by 1%, that is an important finding.

### Reading tonight's output

On the practice data, the top "scam" feature was `long_number`. That is the `<LONG_NUMBER>` tag from the anonymiser, meaning a long transaction ID. The model learnt that fake "you have received money" messages often include a fake transaction ID. That makes sense.

But it also leaned on words like "to" and "is". Those mean nothing. It happened because the practice set is tiny (72 training messages). With little data, models grab whatever happens to correlate. More real data fixes this.

---

## 8. Measuring how good it is (evaluate.py)

Every prediction falls into one of four boxes. This table is the **confusion matrix**:

| | Model says SCAM | Model says LEGIT |
|---|---|---|
| **Really a scam** | True positive: caught it | **False negative: scam slipped through** |
| **Really legit** | **False positive: false alarm** | True negative: correct |

From those counts we get:

- **Precision**: when the model says "scam", how often is it right? Low precision means lots of false alarms, and people stop trusting the tool.
- **Recall**: of all real scams, how many did it catch? Low recall means scams get through. For a safety tool, this is usually the one that hurts most.
- **F1**: one number that balances both. It is only high when both are high.
- **Accuracy**: percentage correct overall. Be careful: if 90% of messages are legit, a useless model that always says "legit" scores 90%. That is why we focus on precision, recall, and F1.

### Why per language?

An overall score of 90% could mean "95% on English, 40% on Twi". The overall number hides that. Breaking it down by language **is the research question of this project**: does the model work for how Ghanaians actually write?

When a slice has under 30 messages, the report marks it "too few to trust". One mistake in 3 messages swings the score by 33%. Being upfront about this is part of doing research honestly.

### errors.csv

Every mistake the model made is saved. Reading them is called **error analysis**, and it is where the real insights come from: "it misses Twi fake-reversal scams because it never saw the word *mfomso* in training."

---

## 9. Tonight's practice run, explained

| Line in the output | What it means |
|---|---|
| `92 rows in, 2 'unsure' set aside` | The 2 messages labelled `unsure` were left out of training and testing |
| `Found 30 template groups` | The 90 remaining messages came from 30 templates (3 near-copies each). The splitter detected all of them. |
| `No template leaks across the split` | No template appears in both training and test. The leakage protection works. |
| `Overall F1 0.857` | Meaningless, because the data is made up. It only proves the code works. |

---

## 10. What comes next (Sprint 2)

The next model is a **transformer**, the technology behind ChatGPT and Claude. Instead of counting words, it reads the whole message and understands context. We will take a transformer already trained on many African languages (such as AfroXLMR) and **fine-tune** it: give it extra training on our scam messages. That needs a GPU, so we will use free Google Colab.

Then we compare: does the transformer beat the baseline, and by how much, in each language?

---

## 11. Interview practice

Try answering these out loud without notes:

1. What problem does your project solve, and why does it matter in Ghana?
2. Where did your data come from, and how did you protect people's privacy?
3. What is data leakage, and how did you prevent it?
4. Why did you start with logistic regression instead of a neural network?
5. What is the difference between precision and recall? Which matters more for scam detection, and why?
6. Why do you report results per language?
7. What were the model's most common mistakes, and why do you think it made them?
8. What are the limitations of your project?

You should be able to answer 1 to 6 after tonight. Questions 7 and 8 come after we have real data.
