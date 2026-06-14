"""
analyzer.py — CSV Data Analyzer
Usage:  python analyzer.py <command> [options]
Run:    python analyzer.py --help
"""
import argparse
import csv
import collections
import os
import statistics
import sys


def _read_csv(path):
    if not os.path.isfile(path):
        sys.exit(f"Error: file not found: {path}")
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            sys.exit("Error: CSV has no header row.")
        fieldnames = list(reader.fieldnames)
        rows = list(reader)
    return fieldnames, rows


def _infer_type(col_values):
    non_null = [v for v in col_values if v.strip()]
    if not non_null:
        return "empty"
    for v in non_null:
        try:
            int(v)
        except ValueError:
            break
    else:
        return "integer"
    for v in non_null:
        try:
            float(v)
        except ValueError:
            return "string"
    return "float"


def _hr(char="─", width=60):
    return char * width


def cmd_profile(args):
    fieldnames, rows = _read_csv(args.file)
    total = len(rows)
    print(f"\nProfiling {os.path.basename(args.file)} …")
    print(_hr())
    print(f"  Rows   : {total:,}")
    print(f"  Columns: {len(fieldnames)}")
    print(_hr())
    col_w = max(len(c) for c in fieldnames)
    print(f"  {'Column':<{col_w}}  {'Type':<8}  {'Nulls':>12}  {'Unique':>8}")
    print(_hr())
    for col in fieldnames:
        vals = [r[col] for r in rows]
        nulls = sum(1 for v in vals if not v.strip())
        non_null = [v for v in vals if v.strip()]
        unique = len(set(non_null))
        typ = _infer_type(non_null)
        null_pct = f"{nulls:,} ({100*nulls/total:.1f}%)" if total else "0"
        print(f"  {col:<{col_w}}  {typ:<8}  {null_pct:>12}  {unique:>8,}")
    print()


def cmd_summarize(args):
    fieldnames, rows = _read_csv(args.file)
    cols = [args.col] if args.col else fieldnames
    found = False
    for col in cols:
        if col not in fieldnames:
            print(f"Warning: column '{col}' not found — skipping.")
            continue
        nums = []
        for r in rows:
            v = r[col].strip()
            if v:
                try:
                    nums.append(float(v))
                except ValueError:
                    pass
        if not nums:
            continue
        found = True
        mn = min(nums)
        mx = max(nums)
        mean = statistics.mean(nums)
        med = statistics.median(nums)
        std = statistics.pstdev(nums)
        q1 = statistics.median(nums[: len(nums) // 2])
        q3 = statistics.median(nums[(len(nums) + 1) // 2 :])
        print(f"\n── {col} ({len(nums):,} values) ──")
        print(f"  Min    : {mn:,.4f}")
        print(f"  Q1     : {q1:,.4f}")
        print(f"  Median : {med:,.4f}")
        print(f"  Mean   : {mean:,.4f}")
        print(f"  Q3     : {q3:,.4f}")
        print(f"  Max    : {mx:,.4f}")
        print(f"  Std    : {std:,.4f}")
    if not found:
        print("No numeric columns found.")


def cmd_filter(args):
    fieldnames, rows = _read_csv(args.file)
    col = args.col
    if col not in fieldnames:
        sys.exit(f"Error: column '{col}' not found. Available: {', '.join(fieldnames)}")

    def matches(row):
        v = row[col]
        if args.eq is not None:
            return v == args.eq
        if args.contains is not None:
            return args.contains.lower() in v.lower()
        try:
            n = float(v)
        except ValueError:
            return False
        if args.gt is not None and n <= args.gt:
            return False
        if args.lt is not None and n >= args.lt:
            return False
        if args.gte is not None and n < args.gte:
            return False
        if args.lte is not None and n > args.lte:
            return False
        return True

    results = [r for r in rows if matches(r)]
    print(f"\n{len(results):,} row(s) matched (of {len(rows):,} total)\n")
    if args.export:
        with open(args.export, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"✓ Exported to {args.export}")
    else:
        if results:
            col_widths = {c: max(len(c), max((len(r[c]) for r in results), default=0)) for c in fieldnames}
            fmt = "  ".join(f"{{:<{col_widths[c]}}}" for c in fieldnames)
            print(fmt.format(*fieldnames))
            print("  ".join("─" * col_widths[c] for c in fieldnames))
            for row in results[: args.limit]:
                print(fmt.format(*[row[c] for c in fieldnames]))
            if len(results) > args.limit:
                print(f"  … {len(results) - args.limit:,} more rows (use --export to save all)")


def cmd_nulls(args):
    fieldnames, rows = _read_csv(args.file)
    null_rows = []
    col_null_counts = collections.Counter()
    for i, row in enumerate(rows, start=2):
        missing = [c for c in fieldnames if not row[c].strip()]
        if missing:
            null_rows.append((i, missing))
            for c in missing:
                col_null_counts[c] += 1
    if not null_rows:
        print("✓ No missing values found.")
        return
    print(f"\n{len(null_rows):,} row(s) with missing values:\n")
    for lineno, cols in null_rows[:50]:
        print(f"  Line {lineno}: missing {', '.join(cols)}")
    if len(null_rows) > 50:
        print(f"  … {len(null_rows) - 50:,} more rows")
    print("\nNull counts by column:")
    for col, count in col_null_counts.most_common():
        pct = 100 * count / len(rows)
        print(f"  {col:<30} {count:>6,}  ({pct:.1f}%)")


def build_parser():
    p = argparse.ArgumentParser(
        prog="analyzer.py",
        description="CSV Data Analyzer — profile, filter, and summarize CSV files",
    )
    sub = p.add_subparsers(dest="command", required=True)

    pp = sub.add_parser("profile", help="Full dataset profile")
    pp.add_argument("file", help="Path to CSV file")

    ps = sub.add_parser("summarize", help="Statistics for numeric columns")
    ps.add_argument("file", help="Path to CSV file")
    ps.add_argument("--col", help="Specific column to summarize")

    pf = sub.add_parser("filter", help="Filter rows by column value")
    pf.add_argument("file", help="Path to CSV file")
    pf.add_argument("--col", required=True, help="Column to filter on")
    pf.add_argument("--eq", help="Exact match")
    pf.add_argument("--contains", help="Substring match (case-insensitive)")
    pf.add_argument("--gt", type=float, help="Greater than (numeric)")
    pf.add_argument("--lt", type=float, help="Less than (numeric)")
    pf.add_argument("--gte", type=float, help="Greater than or equal (numeric)")
    pf.add_argument("--lte", type=float, help="Less than or equal (numeric)")
    pf.add_argument("--export", metavar="FILE", help="Save results to a new CSV")
    pf.add_argument("--limit", type=int, default=50,
                    help="Max rows to print (default: 50)")

    pn = sub.add_parser("nulls", help="Find rows with missing values")
    pn.add_argument("file", help="Path to CSV file")
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    dispatch = {
        "profile":   cmd_profile,
        "summarize": cmd_summarize,
        "filter":    cmd_filter,
        "nulls":     cmd_nulls,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
