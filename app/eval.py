"""Extraction evaluation harness.

This is a *report-only* evaluation tool:
- Runs the pipeline on PDFs in `samples/`
- Compares results to golden expected JSON in `samples/expected/`
- Prints a human-readable report

It does NOT fail CI/tests by default.

Usage:
  python cli.py eval --mode llm

"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.pipeline import process_document
from app.schema import ExtractedData


DEFAULT_SAMPLES_DIR = Path("samples")
DEFAULT_EXPECTED_DIR = Path("samples/expected")


@dataclass
class FieldDiff:
    field: str
    expected: Any
    actual: Any


@dataclass
class SampleReport:
    sample_pdf: Path
    expected_json: Optional[Path]
    passed: bool
    diffs: List[FieldDiff]
    error: Optional[str] = None


def _normalize_date(value: Any) -> Any:
    """Normalize date strings to YYYY-MM-DD when possible."""
    if value is None:
        return None
    if not isinstance(value, str):
        return value

    s = value.strip()
    if not s:
        return None

    # Already ISO-ish
    for fmt in ("%Y-%m-%d",):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass

    # Common US
    for fmt in ("%m/%d/%Y", "%m-%d-%Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass

    # Leave as-is if unknown
    return s


def _normalize_currency(value: Any) -> Any:
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    s = value.strip()
    return s.upper() if s else None


def _normalize_number(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        # round for stable comparisons
        return round(float(value), 2)
    if isinstance(value, str):
        s = value.strip().replace(",", "")
        if not s:
            return None
        try:
            return round(float(s), 2)
        except ValueError:
            return value
    return value


def normalize_extracted(data: Dict[str, Any]) -> Dict[str, Any]:
    """Apply normalization rules for robust field-level comparisons."""
    out = dict(data)

    out["doc_type"] = (out.get("doc_type") or "").strip().lower() or None
    out["vendor"] = (out.get("vendor").strip() if isinstance(out.get("vendor"), str) else out.get("vendor"))
    out["invoice_number"] = (
        out.get("invoice_number").strip() if isinstance(out.get("invoice_number"), str) else out.get("invoice_number")
    )
    out["invoice_date"] = _normalize_date(out.get("invoice_date"))
    out["total_amount"] = _normalize_number(out.get("total_amount"))
    out["currency"] = _normalize_currency(out.get("currency"))

    # Line items: normalize numbers and whitespace
    items = out.get("line_items") or []
    norm_items = []
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            norm_items.append(
                {
                    "description": (item.get("description").strip() if isinstance(item.get("description"), str) else item.get("description")),
                    "quantity": _normalize_number(item.get("quantity")),
                    "unit_price": _normalize_number(item.get("unit_price")),
                    "total": _normalize_number(item.get("total")),
                }
            )
    out["line_items"] = norm_items

    return out


def _load_expected_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _expected_path_for_pdf(pdf_path: Path, expected_dir: Path) -> Path:
    return expected_dir / (pdf_path.stem + ".json")


def compare_fields(expected: Dict[str, Any], actual: Dict[str, Any]) -> List[FieldDiff]:
    """Field-level comparison (normalized)."""
    expected_n = normalize_extracted(expected)
    actual_n = normalize_extracted(actual)

    diffs: List[FieldDiff] = []

    keys = [
        "doc_type",
        "vendor",
        "invoice_number",
        "invoice_date",
        "total_amount",
        "currency",
        "line_items",
    ]

    for k in keys:
        if expected_n.get(k) != actual_n.get(k):
            diffs.append(FieldDiff(field=k, expected=expected_n.get(k), actual=actual_n.get(k)))

    return diffs


def evaluate_samples(
    *,
    mode: str = "llm",
    samples_dir: Path = DEFAULT_SAMPLES_DIR,
    expected_dir: Path = DEFAULT_EXPECTED_DIR,
) -> List[SampleReport]:
    pdfs = sorted(p for p in samples_dir.glob("*.pdf") if p.is_file())
    reports: List[SampleReport] = []

    for pdf_path in pdfs:
        expected_path = _expected_path_for_pdf(pdf_path, expected_dir)
        if not expected_path.exists():
            reports.append(
                SampleReport(
                    sample_pdf=pdf_path,
                    expected_json=None,
                    passed=False,
                    diffs=[],
                    error=f"Missing expected JSON: {expected_path}",
                )
            )
            continue

        try:
            pdf_bytes = pdf_path.read_bytes()
            extracted: ExtractedData = process_document(pdf_bytes, mode=mode)
            actual_dict = extracted.model_dump()
            expected_dict = _load_expected_json(expected_path)
            diffs = compare_fields(expected_dict, actual_dict)
            reports.append(
                SampleReport(
                    sample_pdf=pdf_path,
                    expected_json=expected_path,
                    passed=(len(diffs) == 0),
                    diffs=diffs,
                )
            )
        except Exception as e:
            reports.append(
                SampleReport(
                    sample_pdf=pdf_path,
                    expected_json=expected_path,
                    passed=False,
                    diffs=[],
                    error=str(e),
                )
            )

    return reports


def print_report(reports: List[SampleReport]) -> None:
    total = len(reports)
    passed = sum(1 for r in reports if r.passed)

    print("Extraction Evaluation (report-only)")
    print("=" * 50)
    print(f"Samples: {total} | Passed: {passed} | Failed: {total - passed}")
    print("-")

    for r in reports:
        name = r.sample_pdf.name
        status = "PASS" if r.passed else "FAIL"
        print(f"[{status}] {name}")

        if r.error:
            print(f"  error: {r.error}")
            continue

        if r.diffs:
            for d in r.diffs:
                print(f"  - {d.field}: expected={d.expected!r} actual={d.actual!r}")

    print("=" * 50)

