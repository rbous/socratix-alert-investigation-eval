from __future__ import annotations

import argparse
import dataclasses
import json
import math
from pathlib import Path
from typing import Any, Iterable, Literal


Decision = Literal["close", "review", "escalate"]


@dataclasses.dataclass(frozen=True)
class AlertCase:
    alert_id: str
    scenario: str
    signals: dict[str, Any]
    expected_decision: Decision


@dataclasses.dataclass(frozen=True)
class Investigation:
    alert_id: str
    decision: Decision
    risk_score: float
    risk_band: str
    rationale: list[str]
    evidence_used: list[str]


def load_cases(path: Path) -> list[AlertCase]:
    cases: list[AlertCase] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        cases.append(
            AlertCase(
                alert_id=str(raw["alert_id"]),
                scenario=str(raw["scenario"]),
                signals=dict(raw["signals"]),
                expected_decision=raw["expected_decision"],
            )
        )
    return cases


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def risk_band(score: float) -> str:
    if score >= 0.85:
        return "critical"
    if score >= 0.65:
        return "high"
    if score >= 0.35:
        return "medium"
    return "low"


def baseline_investigator(case: AlertCase) -> Investigation:
    s = case.signals

    score = 0.0
    evidence: list[str] = []
    rationale: list[str] = []

    def add(weight: float, key: str, msg: str) -> None:
        nonlocal score
        value = s.get(key)
        if value is True:
            score += weight
            evidence.append(key)
            rationale.append(msg)
        elif isinstance(value, (int, float)) and value:
            score += weight * float(value)
            evidence.append(key)
            rationale.append(f"{msg} (x{value})")

    add(0.22, "device_new", "New device")
    add(0.20, "ip_geo_mismatch", "IP geo mismatch")
    add(0.18, "velocity_spike", "Velocity spike")
    add(0.16, "chargeback_history", "Chargeback history")
    add(0.14, "email_age_low", "Low email age")
    add(0.14, "synthetic_id_signal", "Synthetic identity signal")
    add(0.12, "merchant_risk_high", "High-risk merchant/category")
    add(0.10, "card_testing_pattern", "Card-testing pattern")
    add(0.10, "multiple_failed_logins", "Multiple failed logins")
    add(0.08, "mule_activity_signal", "Possible mule activity")

    amount = float(s.get("amount_usd", 0.0) or 0.0)
    if amount >= 2000:
        score += 0.14
        evidence.append("amount_usd")
        rationale.append(f"High amount (${amount:,.0f})")
    elif amount >= 500:
        score += 0.08
        evidence.append("amount_usd")
        rationale.append(f"Medium amount (${amount:,.0f})")

    score = clamp01(score)
    band = risk_band(score)

    # Small set of "obvious" patterns that typically deserve escalation in ops workflows.
    amount = float(s.get("amount_usd", 0.0) or 0.0)
    velocity = float(s.get("velocity_spike", 0.0) or 0.0)
    if bool(s.get("card_testing_pattern")) and velocity >= 0.7:
        decision: Decision = "escalate"
        rationale.insert(0, "Pattern match: card testing + velocity spike → escalate.")
    elif bool(s.get("multiple_failed_logins")) and bool(s.get("ip_geo_mismatch")) and bool(s.get("device_new")):
        decision = "escalate"
        rationale.insert(0, "Pattern match: ATO-style login anomaly (fails + geo mismatch + new device) → escalate.")
    elif bool(s.get("chargeback_history")) and amount >= 500:
        decision = "escalate"
        rationale.insert(0, "Pattern match: chargeback history + meaningful amount → escalate.")
    elif bool(s.get("synthetic_id_signal")) and bool(s.get("email_age_low")):
        decision = "escalate"
        rationale.insert(0, "Pattern match: synthetic ID indicators on fresh identity → escalate.")
    elif score >= 0.65:
        decision = "escalate"
    elif score >= 0.35:
        decision = "review"
    else:
        decision = "close"

    if not rationale:
        rationale = ["No strong risk signals triggered in baseline rules."]

    return Investigation(
        alert_id=case.alert_id,
        decision=decision,
        risk_score=score,
        risk_band=band,
        rationale=rationale,
        evidence_used=evidence,
    )


def precision_recall_f1(rows: Iterable[tuple[bool, bool]]) -> dict[str, float]:
    tp = fp = fn = 0
    for predicted_positive, actual_positive in rows:
        if predicted_positive and actual_positive:
            tp += 1
        elif predicted_positive and not actual_positive:
            fp += 1
        elif (not predicted_positive) and actual_positive:
            fn += 1
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "tp": float(tp), "fp": float(fp), "fn": float(fn)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Mini alert-investigation eval harness (offline-first).")
    parser.add_argument("--cases", type=Path, required=True, help="Path to JSONL cases.")
    parser.add_argument("--out", type=Path, required=True, help="Output directory.")
    args = parser.parse_args()

    cases = load_cases(args.cases)
    args.out.mkdir(parents=True, exist_ok=True)

    investigations: list[Investigation] = [baseline_investigator(c) for c in cases]

    # Treat “escalate” as the positive class for a simple regression gate.
    metrics = precision_recall_f1(
        (
            (inv.decision == "escalate", case.expected_decision == "escalate")
            for inv, case in zip(investigations, cases, strict=True)
        )
    )

    report = {
        "agent": "baseline_rules_v1",
        "case_count": len(cases),
        "metrics_escalate": metrics,
        "cases": [
            {
                "alert_id": c.alert_id,
                "scenario": c.scenario,
                "expected_decision": c.expected_decision,
                "predicted": dataclasses.asdict(inv),
                "signals": c.signals,
            }
            for c, inv in zip(cases, investigations, strict=True)
        ],
    }

    (args.out / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Founder-skimmable markdown report.
    lines: list[str] = []
    lines.append("# Socratix alert-investigation eval (mini)\n")
    lines.append(f"- Agent: `{report['agent']}`")
    lines.append(f"- Cases: `{report['case_count']}`")
    lines.append(
        "- Escalate metrics (treating `escalate` as positive): "
        + f"precision={metrics['precision']:.2f}, recall={metrics['recall']:.2f}, f1={metrics['f1']:.2f}"
    )
    lines.append("")
    lines.append("## Case-by-case\n")
    for entry in report["cases"]:
        pred = entry["predicted"]
        lines.append(f"### {entry['alert_id']}: {entry['scenario']}")
        lines.append(f"- Expected: `{entry['expected_decision']}` | Predicted: `{pred['decision']}` | Risk: `{pred['risk_score']:.2f}` ({pred['risk_band']})")
        lines.append(f"- Evidence used: {', '.join(pred['evidence_used']) if pred['evidence_used'] else '(none)'}")
        for r in pred["rationale"]:
            lines.append(f"  - {r}")
        lines.append("")

    (args.out / "report.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    print(args.out / "report.md")


if __name__ == "__main__":
    main()
