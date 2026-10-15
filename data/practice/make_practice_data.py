"""
Builds a small MADE-UP practice dataset.

WHY THIS EXISTS
We need some data to check that the code works before the real messages
are collected. This file writes fake messages so we can run the whole
pipeline tonight.

IMPORTANT
- Every row here is marked is_synthetic = "yes" and source = "practice".
- These messages are NEVER used to report results. Real results only come
  from real, collected messages.
- The Twi lines are rough and were not written by a native speaker. They
  only exist so the per-language code has something to count.

Some messages are deliberately near-copies of each other (same template,
different amount or number). That lets us test that the splitter keeps
copies together, which is what happens with real scam templates.

Run:  python data/practice/make_practice_data.py
"""

import csv
import random
from pathlib import Path

random.seed(42)  # same "random" choices every time, so results are repeatable

OUT = Path(__file__).parent / "practice_messages.csv"

# Each entry: (text, label, scam_type, language)
# {amt} and {num} are filled in with random values to create near-copies.
SCAM_TEMPLATES = [
    ("Dear customer you have receive GHS {amt}.00 from 0{num}. Your new balance is GHS {amt}.50. Transaction ID 7{num}", "fake_reversal", "en"),
    ("Please i mistakenly send GHS {amt} to your number. Kindly send it back to 0{num} God bless you", "fake_reversal", "en"),
    ("Chale abeg I send {amt} cedis to your momo by mistake, abeg reverse am give me for 0{num}", "fake_reversal", "pcm"),
    ("MTN MoMo: Your account will be blocked today. Call 0{num} to verify your PIN and avoid suspension", "impersonation", "en"),
    ("Telecel Cash alert: your wallet is under review. Send your PIN to 0{num} to keep it active", "impersonation", "en"),
    ("Congratulations! Your number won GHS {amt} in the MoMo promo. Send GHS 50 processing fee to 0{num} to claim", "prize_lottery", "en"),
    ("Massa you don win {amt} cedis for the promo o, send 30 cedis make dem release am. Call 0{num}", "prize_lottery", "pcm"),
    ("Your OTP is needed to complete your MoMo upgrade. Reply with the code sent to you now", "otp_pin_request", "en"),
    ("Get instant loan of GHS {amt} with no collateral. Pay GHS 100 registration to 0{num} today", "loan_investment", "en"),
    ("Invest GHS {amt} today and get double by Friday. Limited slots, send to 0{num}", "loan_investment", "en"),
    ("Hiring now! Data entry job GHS {amt} monthly. Pay GHS 80 form fee to 0{num} to start", "job_offer", "en"),
    ("Mummy this is my new number, my phone spoil. Please send me {amt} cedis urgent", "family_emergency", "en"),
    ("Mepa wo kyew, mede sika GHS {amt} too wo momo mfomso. San de ma me 0{num}", "fake_reversal", "tw"),
    ("Wo anya GHS {amt} wo promo no mu. Fre 0{num} na wo nya wo sika", "prize_lottery", "tw"),
    ("Hello please I send you {amt} cedis by mistake, mepa wo kyew san de ma me", "fake_reversal", "mixed"),
    ("Your MoMo don block o, call 0{num} make dem unblock am, wo nya ntem", "impersonation", "mixed"),
]

LEGIT_TEMPLATES = [
    ("Payment received for GHS {amt}.00 from KWAME ASANTE. Current Balance: GHS {amt}.40. Transaction ID: 4{num}.", "en"),
    ("Buy 5GB for GHS 10 valid for 7 days. Dial *138# to enjoy", "en"),
    ("Your bill payment of GHS {amt} to ECG was successful. Thank you for using MoMo", "en"),
    ("Hi, are we still meeting at 4pm tomorrow?", "en"),
    ("Please call me when you are free, nothing serious", "en"),
    ("Reminder: CSA will never ask for your PIN. Report scams on 292", "en"),
    ("Chale I dey come, make you wait small", "pcm"),
    ("Abeg send me the notes from class when you get chance", "pcm"),
    ("How far, you reach house?", "pcm"),
    ("Mepa wo kyew fre me bere a wo wie", "tw"),
    ("Ete sen? Me ba fie anwummere", "tw"),
    ("I'm at the market, wo pe biribi?", "mixed"),
    ("Mummy I don reach school safely, I will call you later", "pcm"),
    ("Your MoMo cash out of GHS {amt} at agent 0{num} was successful", "en"),
]

rows = []
next_id = 1

def rand_num():
    return str(random.randint(20_000_000, 59_999_999))

def rand_amt():
    return str(random.choice([50, 100, 150, 200, 300, 450, 500, 1000, 1500]))

# Make 3 near-copies of each scam template and 3 of each legit template
for text, scam_type, lang in SCAM_TEMPLATES:
    for _ in range(3):
        rows.append({
            "id": next_id,
            "text": text.format(amt=rand_amt(), num=rand_num()),
            "label": "scam", "scam_type": scam_type, "language": lang,
            "source": "practice", "channel": "sms", "is_synthetic": "yes", "notes": "",
        })
        next_id += 1

for text, lang in LEGIT_TEMPLATES:
    for _ in range(3):
        rows.append({
            "id": next_id,
            "text": text.format(amt=rand_amt(), num=rand_num()),
            "label": "legit", "scam_type": "", "language": lang,
            "source": "practice", "channel": "sms", "is_synthetic": "yes", "notes": "",
        })
        next_id += 1

# A couple of "unsure" rows, to show they get set aside
rows.append({"id": next_id, "text": "Call me now its urgent", "label": "unsure", "scam_type": "",
             "language": "en", "source": "practice", "channel": "sms", "is_synthetic": "yes", "notes": "no context"})
next_id += 1
rows.append({"id": next_id, "text": "Send it to this number 0244000000", "label": "unsure", "scam_type": "",
             "language": "en", "source": "practice", "channel": "sms", "is_synthetic": "yes", "notes": "no context"})

random.shuffle(rows)

with OUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} practice rows to {OUT}")
