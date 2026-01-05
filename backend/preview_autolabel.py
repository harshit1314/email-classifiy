#!/usr/bin/env python3
"""Preview weak-labeling counts using the same keyword heuristics as the trainer.

Usage:
  python backend/preview_autolabel.py backend/enron_parsed.csv
"""
import sys
import csv
from collections import defaultdict
import os


categories = ["spam", "important", "promotion", "social", "updates"]

keywords = {
    "spam": ["win", "claim", "prize", "free", "buy now", "click here", "lottery", "inheritance", "viagra", "earn ", "make money"],
    "important": ["meeting", "deadline", "urgent", "invoice", "signature", "approval", "security", "breach", "client", "legal"],
    "promotion": ["sale", "discount", "offer", "coupon", "free shipping", "promotion", "deal", "buy", "save"],
    "social": ["invite", "party", "birthday", "hangout", "photo", "friend", "rsvp", "concert"],
    "updates": ["order", "confirmation", "receipt", "shipping", "tracking", "subscription", "password reset", "notification"],
}


def auto_label_text(text: str):
    text_l = (text or "").lower()
    counts = {cat: 0 for cat in categories}
    for cat, kws in keywords.items():
        for kw in kws:
            if kw in text_l:
                counts[cat] += 1
    best_cat = max(counts, key=counts.get)
    if counts[best_cat] > 0:
        return best_cat
    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python preview_autolabel.py parsed.csv")
        sys.exit(1)
    path = sys.argv[1]
    if not os.path.exists(path):
        print("File not found:", path)
        sys.exit(2)

    counts = defaultdict(int)
    samples = defaultdict(list)
    total = 0
    # increase CSV field size limit to handle long bodies
    try:
        csv.field_size_limit(sys.maxsize)
    except Exception:
        try:
            csv.field_size_limit(10 * 1024 * 1024)
        except Exception:
            pass

    with open(path, 'r', encoding='utf-8', errors='replace', newline='') as f:
        reader = csv.DictReader(f)
        for r in reader:
            total += 1
            text = (r.get('body') or r.get('message') or r.get('text') or '')
            lbl = auto_label_text(text)
            if lbl:
                counts[lbl] += 1
                if len(samples[lbl]) < 3:
                    samples[lbl].append((r.get('id'), r.get('file'), (text or '')[:300].replace('\n',' ')))

    print(f"Total rows: {total}")
    for cat in categories:
        print(f"{cat}: {counts.get(cat,0)}")
        for s in samples.get(cat, []):
            print(f"  sample id={s[0]} file={s[1]} text={s[2]}")


if __name__ == '__main__':
    main()
