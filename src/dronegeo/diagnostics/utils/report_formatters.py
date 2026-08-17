"""
dronegeo.diagnostics.utils.report_formatters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Report serialization and visualization formatting for AutoQC findings.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List


def format_markdown_report(
    dataset_path: str,
    dataset_type: str,
    quality_score: int,
    overall_status: str,
    summary_metrics: Dict[str, Any],
    issues: List[Dict[str, Any]],
) -> str:
    """Generates a GitHub-flavored Markdown diagnostic and QC report."""
    lines = [
        "# 🔍 DroneGeo AutoQC: Diagnostic & Survey Health Report",
        "",
        f"- **Dataset**: `{Path(dataset_path).name}`",
        f"- **Type**: `{dataset_type}`",
        f"- **AutoQC Quality Score**: **{quality_score}/100** ({overall_status})",
        "",
        "## 📊 Summary Metrics",
        "| Metric | Value |",
        "| :--- | :--- |",
    ]
    for k, v in summary_metrics.items():
        formatted_val = f"{v:,.2f}" if isinstance(v, float) else str(v)
        lines.append(f"| `{k}` | {formatted_val} |")

    lines.extend([
        "",
        f"## 🔍 Diagnostic Findings ({len(issues)} issues detected)",
        "",
    ])

    if not issues:
        lines.append("> [!NOTE]\n> ✅ No defects detected. Dataset meets survey-grade tolerances.")
    else:
        for i, issue in enumerate(issues, 1):
            sev = issue.get("severity", "INFO")
            icon = "🔴" if sev == "CRITICAL" else ("🟡" if sev == "WARNING" else "ℹ️")
            lines.extend([
                f"### {i}. {icon} [{issue.get('code')}] {issue.get('title')}",
                f"- **Severity**: `{sev}`",
                f"- **What Was Found**: {issue.get('description')}",
                f"- **Physical Root Cause**: {issue.get('root_cause')}",
                f"- **Downstream Impact**: {issue.get('impact')}",
                f"- **Prescribed AutoQC Fix & Parameters**:",
                f"  ```python",
                f"  {json.dumps(issue.get('suggested_parameters', {}), indent=2)}",
                f"  ```",
                "",
            ])

    lines.extend([
        "## 🛠️ Automated AutoQC Remediation",
        "To auto-heal this dataset with prescribed parameters:",
        "```python",
        "import dronegeo as dg",
        "",
        f"repaired_path = dg.autoqc.remediate(",
        f"    input_path='{dataset_path}',",
        f"    output_path='healed_{Path(dataset_path).name}'",
        ")",
        "```",
    ])

    return "\n".join(lines)


def format_terminal_summary(
    dataset_path: str,
    dataset_type: str,
    quality_score: int,
    overall_status: str,
    summary_metrics: Dict[str, Any],
    issues: List[Dict[str, Any]],
) -> None:
    """Prints a structured summary to the terminal."""
    print("=" * 75)
    print(f"🔍 DroneGeo AutoQC: {Path(dataset_path).name}")
    print("=" * 75)
    print(f"AutoQC Quality Score : {quality_score}/100 [{overall_status}]")
    print(f"Dataset Type         : {dataset_type}")
    print("\nKey Metrics:")
    for k, v in summary_metrics.items():
        formatted_val = f"{v:,.2f}" if isinstance(v, float) else str(v)
        print(f"  * {k:24s}: {formatted_val}")

    if not issues:
        print("\n[OK] Clean dataset - No anomalies or defects found.")
    else:
        print(f"\nIssues Detected ({len(issues)}):")
        for idx, issue in enumerate(issues, 1):
            print(f"\n  [{idx}] {issue.get('severity')}: {issue.get('title')} ({issue.get('code')})")
            print(f"      Description : {issue.get('description')}")
            print(f"      Root Cause  : {issue.get('root_cause')}")
            print(f"      Impact      : {issue.get('impact')}")
            print(f"      Prescription: {issue.get('suggested_parameters')}")
    print("=" * 75)
