"""
test_analyzer.py — tests for CSV Data Analyzer
Run:  pytest test_analyzer.py -v
"""
import csv
import os
import pytest
import analyzer as mod


def _make_csv(tmp_path, name, header, rows):
    path = tmp_path / name
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    return str(path)


# ── helpers ────────────────────────────────────────────────────────────────────

def test_infer_integer():
    assert mod._infer_type(["1", "2", "42"]) == "integer"

def test_infer_float():
    assert mod._infer_type(["1.5", "3.14"]) == "float"

def test_infer_string():
    assert mod._infer_type(["hello", "world"]) == "string"

def test_infer_empty():
    assert mod._infer_type([]) == "empty"


# ── profile ────────────────────────────────────────────────────────────────────

class TestProfile:
    def test_basic(self, tmp_path, capsys):
        path = _make_csv(tmp_path, "data.csv",
                         ["name", "age", "salary"],
                         [["Alice", "30", "90000"], ["Bob", "", "65000"]])
        args = mod.build_parser().parse_args(["profile", path])
        mod.cmd_profile(args)
        out = capsys.readouterr().out
        assert "2" in out
        assert "name" in out and "age" in out

    def test_missing_file_exits(self):
        args = mod.build_parser().parse_args(["profile", "/no/such/file.csv"])
        with pytest.raises(SystemExit):
            mod.cmd_profile(args)

    def test_null_detection(self, tmp_path, capsys):
        path = _make_csv(tmp_path, "n.csv", ["a", "b"],
                         [["1", ""], ["2", "ok"]])
        args = mod.build_parser().parse_args(["profile", path])
        mod.cmd_profile(args)
        out = capsys.readouterr().out
        assert "b" in out


# ── summarize ──────────────────────────────────────────────────────────────────

class TestSummarize:
    def test_numeric_column(self, tmp_path, capsys):
        path = _make_csv(tmp_path, "nums.csv", ["val"],
                         [["10"], ["20"], ["30"]])
        args = mod.build_parser().parse_args(["summarize", path])
        mod.cmd_summarize(args)
        out = capsys.readouterr().out
        assert "val" in out and "20" in out

    def test_specific_col(self, tmp_path, capsys):
        path = _make_csv(tmp_path, "emp.csv", ["name", "salary"],
                         [["Alice", "90000"], ["Bob", "60000"]])
        args = mod.build_parser().parse_args(["summarize", path, "--col", "salary"])
        mod.cmd_summarize(args)
        out = capsys.readouterr().out
        assert "salary" in out and "60000" in out

    def test_no_numeric_cols(self, tmp_path, capsys):
        path = _make_csv(tmp_path, "text.csv", ["word"],
                         [["hello"], ["world"]])
        args = mod.build_parser().parse_args(["summarize", path])
        mod.cmd_summarize(args)
        assert "No numeric" in capsys.readouterr().out


# ── filter ─────────────────────────────────────────────────────────────────────

class TestFilter:
    def _emp(self, tmp_path):
        return _make_csv(tmp_path, "emp.csv",
                         ["name", "dept", "salary"],
                         [["Alice", "Engineering", "95000"],
                          ["Bob", "Marketing", "65000"],
                          ["Carol", "Engineering", "80000"]])

    def test_eq(self, tmp_path, capsys):
        path = self._emp(tmp_path)
        args = mod.build_parser().parse_args(
            ["filter", path, "--col", "dept", "--eq", "Marketing"])
        mod.cmd_filter(args)
        out = capsys.readouterr().out
        assert "1" in out and "Bob" in out

    def test_contains(self, tmp_path, capsys):
        path = self._emp(tmp_path)
        args = mod.build_parser().parse_args(
            ["filter", path, "--col", "name", "--contains", "al"])
        mod.cmd_filter(args)
        assert "2" in capsys.readouterr().out

    def test_gt(self, tmp_path, capsys):
        path = self._emp(tmp_path)
        args = mod.build_parser().parse_args(
            ["filter", path, "--col", "salary", "--gt", "80000"])
        mod.cmd_filter(args)
        assert "1" in capsys.readouterr().out

    def test_export(self, tmp_path, capsys):
        path = self._emp(tmp_path)
        out_path = str(tmp_path / "out.csv")
        args = mod.build_parser().parse_args(
            ["filter", path, "--col", "dept", "--eq", "Engineering",
             "--export", out_path])
        mod.cmd_filter(args)
        assert os.path.isfile(out_path)
        with open(out_path) as f:
            content = f.read()
        assert "Alice" in content and "Carol" in content
        assert "Bob" not in content

    def test_missing_col_exits(self, tmp_path):
        path = self._emp(tmp_path)
        args = mod.build_parser().parse_args(
            ["filter", path, "--col", "nonexistent", "--eq", "x"])
        with pytest.raises(SystemExit):
            mod.cmd_filter(args)


# ── nulls ──────────────────────────────────────────────────────────────────────

class TestNulls:
    def test_no_nulls(self, tmp_path, capsys):
        path = _make_csv(tmp_path, "clean.csv", ["a", "b"],
                         [["1", "x"], ["2", "y"]])
        args = mod.build_parser().parse_args(["nulls", path])
        mod.cmd_nulls(args)
        assert "No missing" in capsys.readouterr().out

    def test_finds_nulls(self, tmp_path, capsys):
        path = _make_csv(tmp_path, "gaps.csv", ["a", "b"],
                         [["1", ""], ["", "y"]])
        args = mod.build_parser().parse_args(["nulls", path])
        mod.cmd_nulls(args)
        assert "2" in capsys.readouterr().out
