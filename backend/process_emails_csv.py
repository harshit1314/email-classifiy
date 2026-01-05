#!/usr/bin/env python3
"""Parse raw messages in a CSV `message` column into structured CSV for training.

Usage:
  python backend/process_emails_csv.py backend/emails.csv backend/enron_parsed.csv

Output columns: `id`, `file`, `from`, `to`, `subject`, `date`, `body`
"""
import sys
import csv
from email import policy
from email.parser import Parser
import os


def extract_body(msg):
    try:
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                if ctype == 'text/plain' and not part.get_content_disposition():
                    return part.get_content()
            for part in msg.walk():
                if part.get_content_type().startswith('text/'):
                    return part.get_content()
            return ''
        else:
            return msg.get_content()
    except Exception:
        return ''


def process(in_csv, out_csv, sample_rows=5):
    total = 0
    written = 0
    samples = []
    parser = Parser(policy=policy.default)

    # Increase CSV field size limit to handle large raw message fields
    try:
        csv.field_size_limit(sys.maxsize)
    except Exception:
        try:
            csv.field_size_limit(10 * 1024 * 1024)
        except Exception:
            pass

    with open(in_csv, 'r', encoding='utf-8', errors='replace', newline='') as inf:
        reader = csv.DictReader(inf)
        rows = list(reader)

    with open(out_csv, 'w', encoding='utf-8', newline='') as outf:
        fieldnames = ['id', 'file', 'from', 'to', 'subject', 'date', 'body']
        writer = csv.DictWriter(outf, fieldnames=fieldnames)
        writer.writeheader()

        for i, r in enumerate(rows):
            total += 1
            raw = r.get('message') or r.get('Message') or ''
            try:
                msg = parser.parsestr(raw)
            except Exception:
                # fallback: wrap as simple plain text
                msg = parser.parsestr('Subject: \n\n' + raw)

            body = extract_body(msg)
            out = {
                'id': i,
                'file': r.get('file', ''),
                'from': msg.get('From', '') or msg.get('from', ''),
                'to': msg.get('To', '') or msg.get('to', ''),
                'subject': msg.get('Subject', '') or msg.get('subject', ''),
                'date': msg.get('Date', '') or msg.get('date', ''),
                'body': body.replace('\r\n', '\n') if isinstance(body, str) else ''
            }
            writer.writerow(out)
            written += 1
            if len(samples) < sample_rows:
                samples.append(out)

    print(f"Processed {total} rows, wrote {written} parsed messages to: {out_csv}")
    print("Sample parsed rows:")
    for s in samples:
        print('---')
        print(f"id: {s['id']}, file: {s['file']}, subject: {s['subject']}")
        print(s['body'][:400].replace('\n', ' '))


def main():
    if len(sys.argv) < 3:
        print("Usage: python process_emails_csv.py input.csv output.csv")
        sys.exit(1)
    inp = sys.argv[1]
    out = sys.argv[2]
    if not os.path.exists(inp):
        print(f"Input file not found: {inp}")
        sys.exit(2)
    process(inp, out)


if __name__ == '__main__':
    main()
