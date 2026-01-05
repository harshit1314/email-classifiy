#!/usr/bin/env python3
"""Aggregate Enron dataset message files into a single CSV.

Usage:
  python backend/enron_to_csv.py /path/to/enron_root backend/enrons_emails.csv

The script walks the directory tree, parses files with the email parser,
and writes a CSV with columns: `filename`, `from`, `to`, `subject`, `date`, `body`.
"""
import sys
import os
import csv
from email import policy
from email.parser import BytesParser


def iter_message_files(root):
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if fname.lower().endswith(('.txt', '.eml')):
                yield os.path.join(dirpath, fname)


def extract_body(msg):
    # Prefer plain text body
    try:
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                if ctype == 'text/plain' and not part.get_content_disposition():
                    return part.get_content()
            # fallback to first text/*
            for part in msg.walk():
                if part.get_content_type().startswith('text/'):
                    return part.get_content()
            return ''
        else:
            return msg.get_content()
    except Exception:
        return ''


def main():
    if len(sys.argv) < 3:
        print("Usage: python enron_to_csv.py /path/to/enron_root out.csv")
        sys.exit(1)

    root = sys.argv[1]
    out_csv = sys.argv[2]

    if not os.path.isdir(root):
        print(f"Not a directory: {root}")
        sys.exit(2)

    rows = []
    parser = BytesParser(policy=policy.default)
    for path in iter_message_files(root):
        try:
            with open(path, 'rb') as f:
                msg = parser.parse(f)
        except Exception:
            continue

        body = extract_body(msg)
        rows.append({
            'filename': os.path.relpath(path, root),
            'from': msg.get('From', ''),
            'to': msg.get('To', ''),
            'subject': msg.get('Subject', ''),
            'date': msg.get('Date', ''),
            'body': body.replace('\r\n', '\n') if isinstance(body, str) else ''
        })

    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['filename', 'from', 'to', 'subject', 'date', 'body'])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"Wrote {len(rows)} messages to {out_csv}")


if __name__ == '__main__':
    main()
