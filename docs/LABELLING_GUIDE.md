# Labelling Guide

This guide is the rulebook for labelling messages. Every message must be labelled the same way, by anyone, every time. If two people would label the same message differently, the guide needs a clearer rule.

Why this matters: the model learns only from our labels. If our labels are inconsistent, the model learns confusion.

---

## 1. The data format

Every message is one row in a CSV file (a spreadsheet saved as plain text). You can fill it in Google Sheets or Excel, then download it as CSV.

| Column | What to put | Example |
|---|---|---|
| `id` | A unique number for the message | `17` |
| `text` | The message, copied exactly (spelling mistakes included) | `Dear customer you have receive GHS 500...` |
| `label` | `scam`, `legit`, or `unsure` | `scam` |
| `scam_type` | One type from section 3 (leave empty if legit) | `fake_reversal` |
| `language` | `en`, `pcm`, `tw`, or `mixed` (see section 4) | `pcm` |
| `source` | Where it came from (see section 5) | `friend` |
| `channel` | `sms`, `whatsapp`, `social`, or `other` | `sms` |
| `is_synthetic` | `no` for real messages. `yes` for anything made up, translated, or rewritten | `no` |
| `notes` | Anything odd or worth remembering | `came with a follow-up call` |

**Copy the text exactly.** Do not fix spelling or grammar. Scammers' spelling mistakes are a real signal the model can learn from.

Do not worry about phone numbers or names in the text. The anonymiser script removes them. But do not share the raw file with anyone.

---

## 2. The three labels

### `scam`
The message tries to get money, a PIN, an OTP, or account access through deception.

Ask yourself: **if the person did what this message asks, would they lose money or control of their account to someone lying to them?** If yes, it is a scam.

### `legit`
A genuine message. This includes real MoMo transaction alerts, real telco promotions, and normal messages from friends and family, **even ones asking for money**.

We need lots of legit messages. A model that has only seen scams will think everything is a scam.

### `unsure`
You cannot tell. Use this honestly instead of guessing. These rows are kept out of training and testing, and we report how many there were.

---

## 3. Scam types

Pick the closest one:

| `scam_type` | What it looks like |
|---|---|
| `fake_reversal` | Fake "you have received money" alert, followed by "I sent it by mistake, please send it back" |
| `impersonation` | Pretends to be MTN, Telecel, AT, a bank, the police, or a government body |
| `prize_lottery` | "You have won", "promo winner", "claim your reward" |
| `otp_pin_request` | Asks for your PIN, OTP, or verification code |
| `loan_investment` | Fake loans with an upfront fee, "double your money", fake investment |
| `job_offer` | Fake jobs or scholarships that need a registration fee |
| `family_emergency` | Pretends to be a relative or friend in trouble, from an unknown number |
| `other` | Anything that does not fit (explain in `notes`) |

---

## 4. Language tags

| Tag | Meaning |
|---|---|
| `en` | English only (including Ghanaian English with errors) |
| `pcm` | Ghanaian Pidgin only. "pcm" is the standard code for Pidgin. |
| `tw` | Twi only |
| `mixed` | Two or more languages mixed in one message, such as English with some Twi words |

**Rule:** if a message is mostly one language with one or two borrowed words that everyone uses (like "chale" in an English sentence), tag the main language. If it really switches between languages, tag `mixed`.

---

## 5. Source tags

| `source` | Meaning |
|---|---|
| `own_phone` | From your own phone |
| `friend` | A friend or family member shared it with permission |
| `public_post` | A screenshot or text someone posted publicly (X, Facebook, TikTok, Reddit) |
| `public_alert` | A warning published by CSA, a telco, a bank, or the media |
| `practice` | Made up for testing the code only. Never used for results. |

---

## 6. The hard cases

These are where labellers disagree. Decide them using these rules:

1. **Real MoMo transaction alert** (from the official sender, matches a real transaction): `legit`.
2. **Message that looks like a MoMo alert but arrived from a normal phone number**: `scam`, type `fake_reversal` or `impersonation`. In the `notes` column, write that the sender was a normal number, since the model only sees the text.
3. **Real telco promotion** ("Buy 5GB for GHS 10"): `legit`. Annoying is not the same as a scam.
4. **Friend or family asking for money from a number you know**: `legit`.
5. **"Mum, this is my new number, send me money urgently"** from an unknown number: `scam`, type `family_emergency`.
6. **A message warning people about scams** (for example from CSA): `legit`. It mentions scams but is not one.
7. **You only have the reply, not the original scam message**: skip it.

When you meet a new hard case, write the decision here so the rule stays consistent.

---

## 7. Privacy rules

- Get permission before taking messages from someone else's phone.
- Never commit raw data to GitHub. The `.gitignore` file already blocks `data/raw/`.
- Run the anonymiser before sharing any file with anyone.
