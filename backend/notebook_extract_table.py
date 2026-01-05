#!/usr/bin/env python3
"""Extract first HTML table from a Jupyter notebook's outputs and save to CSV.

Usage:
  python backend/notebook_extract_table.py path/to/Email_classification.ipynb.txt [output.csv]

This script looks for `text/html` outputs (pandas DataFrame HTML from `df.head()`)
and saves the largest table found to CSV. If no HTML tables are found it will exit
with a message.
"""
import json
import sys
from io import StringIO
import os

try:
    import pandas as pd
except ImportError:
    print("Please install pandas: pip install pandas")
    raise


def extract_tables(nb_path):
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    tables = []
    for cell in nb.get('cells', []):
        for out in cell.get('outputs', []):
            data = out.get('data') or {}
            # HTML output from pandas (df.head())
            html = data.get('text/html')
            if html:
                html_str = ''.join(html) if isinstance(html, list) else html
                try:
                    dfs = pd.read_html(StringIO(html_str))
                    tables.extend(dfs)
                except Exception:
                    continue

            # Some outputs embed full HTML in text/plain
            text_plain = data.get('text/plain')
            if text_plain:
                txt = ''.join(text_plain) if isinstance(text_plain, list) else text_plain
                if '<table' in txt:
                    try:
                        dfs = pd.read_html(StringIO(txt))
                        tables.extend(dfs)
                    except Exception:
                        continue

    return tables


def pick_largest_table(tables):
    if not tables:
        return None
    # choose by number of rows, then by number of columns
    tables_sorted = sorted(tables, key=lambda d: (len(d.index), len(d.columns)), reverse=True)
    return tables_sorted[0]


def main():
    if len(sys.argv) < 2:
        print("Usage: python notebook_extract_table.py path/to/notebook.ipynb.txt [out.csv]")
        sys.exit(1)

    nb_path = sys.argv[1]
    out_csv = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(nb_path), 'emails.csv')

    if not os.path.exists(nb_path):
        print(f"Notebook file not found: {nb_path}")
        sys.exit(2)

    tables = extract_tables(nb_path)
    if not tables:
        print("No HTML tables found in notebook outputs. Try running the notebook and producing a DataFrame output (df.head()) or provide the CSV directly.")
        sys.exit(3)

    df = pick_largest_table(tables)
    if df is None or df.empty:
        print("No usable table found in notebook outputs.")
        sys.exit(4)

    df.to_csv(out_csv, index=False)
    print(f"Saved extracted table with {len(df)} rows and {len(df.columns)} columns to: {out_csv}")


if __name__ == '__main__':
    main()
