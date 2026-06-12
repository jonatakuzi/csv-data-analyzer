# CSV Data Analyzer

A Python command-line tool for profiling, filtering, and summarizing CSV datasets. Handles files with thousands of rows in seconds — no pandas, no pip installs required.

![Python](https://img.shields.io/badge/Python-3.7%2B-blue?logo=python&logoColor=white)
![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

- **Profile** any CSV — row count, column names, inferred types, null counts, and unique value stats
- **Summarize** numeric columns — min, max, mean, median, standard deviation
- **Filter** rows by column value (exact match, substring, or numeric comparison)
- **Detect nulls** — flag every row with missing values and which columns are affected
- **Export** filtered results to a new CSV file
- Zero external dependencies — uses only Python's `csv`, `statistics`, and `argparse` modules

## Requirements

- Python 3.7+
- No `pip install` needed

## Installation

```bash
git clone https://github.com/jonatakuzi/csv-data-analyzer.git
cd csv-data-analyzer
```

## Usage

### Profile a CSV file
```bash
python analyzer.py profile data.csv
```
```
Profiling data.csv...
─────────────────────────────────────────
Rows:        1,247
Columns:     6
─────────────────────────────────────────
Column        Type    Nulls   Unique
─────────────────────────────────────────
name          str     0       1247
age           int     3       47
salary        float   12      891
department    str     0       6
status        str     0       2
hire_date     str     1       489
```

### Summarize numeric columns
```bash
python analyzer.py summarize data.csv
python analyzer.py summarize data.csv --col salary
```

### Filter rows
```bash
# Exact match
python analyzer.py filter data.csv --col status --eq active

# Numeric comparison
python analyzer.py filter data.csv --col salary --gt 60000

# Substring match
python analyzer.py filter data.csv --col name --contains Smith
```

### Export filtered results
```bash
python analyzer.py filter data.csv --col status --eq active --export filtered.csv
```

### Find rows with missing values
```bash
python analyzer.py nulls data.csv
```

## Tech Stack

- Python 3.7+
- Standard library: `csv`, `statistics`, `argparse`, `collections`
