# Socratix Alert-Investigation Eval Harness (Mini)

Tiny runnable harness to score an “AI fraud analyst” on alert investigation cases with:

- structured decisions (`close` / `review` / `escalate`)
- risk score + calibrated bands
- evidence trace (which signals were used)
- regression-friendly metrics (precision/recall on “escalate”)

This is intentionally small and offline-first (no API keys required). If you want to plug in an LLM investigator later, there’s a stub interface in `alert_eval.py`.

## Quickstart (Windows / PowerShell)

```powershell
$PY="C:\Users\rbous\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $PY targets\socratix-ai\demo\alert_eval.py --cases targets\socratix-ai\demo\data\cases.jsonl --out targets\socratix-ai\demo\out
```

Outputs:

- `out/report.md` (founder-skimmable)
- `out/report.json` (machine-readable)

## What to change for “real” use

- Replace `data/cases.jsonl` with a redacted slice of real alerts + analyst dispositions.
- Add connectors for evidence sources (device graph, account history, velocity rules, chargeback outcomes).
- Run the harness in CI for every agent/prompt change; fail on metric regressions or schema violations.

Describe the proof-of-work demo here.

## Run

```bash
# command
```

## What It Shows

- 
