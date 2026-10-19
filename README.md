# Which Campaign Actually Creates More Sales?

A portfolio project analyzing the published Hillstrom email experiment with **SQL + Python**, plus an optional **DeepSeek Experiment Review Agent** and **Jev evidence assessment**. Power BI is excluded. Excel is unnecessary; generated CSVs can be opened in Excel if desired.

The business question: did assigning customers to either email campaign cause extra purchases or revenue compared with sending no email?

## Start here (Windows PowerShell)

**Recommended: one command for a complete run.** From the cloned repository folder:

```powershell
.\run.cmd
```

The launcher prepares missing dependencies, obtains/validates the source, runs SQL and statistics, uses configured DeepSeek/Jev keys, creates a new dated visual report, and opens that report in your browser. No virtual-environment activation or execution-policy change is needed. Each run preserves earlier reports under `reports/runs/`; run history (reports/index.html, generated locally) lists them. See the [zero-to-end guide](docs/RUN_FROM_ZERO.md).

For individual steps and development:

```powershell
# Run from the cloned repository folder.
# First-time setup, if .venv has not already been prepared:
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Download the public source, then reproduce the analysis:
.\.venv\Scripts\python.exe project.py download
.\.venv\Scripts\python.exe project.py analyze
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

No activation or machine-wide configuration changes are required. Use Python 3.11 or newer. `requirements-lock.txt`, when present, records the environment verified during setup; install it instead of `requirements.txt` to reproduce those dependency versions.

Read [the analysis plan](docs/experiment_plan.md) before interpreting results. Open [the generated decision report](reports/decision_report.md) after running the analysis.

For a quick visual explanation, open **[Results at a glance](reports/dashboard.html)** in your browser. The page works offline without a server. Switch between purchases and revenue to see group rates, estimated effects, and uncertainty. `analyze` regenerates it from the same calculated results; no AI API calls are needed.

The [final case-study recommendation](docs/final_recommendation.md) explains the proposed business action and its limits: both historical campaign comparisons show positive evidence, while a fresh controlled experiment is recommended before acting on today's customers.

## Files and outputs

| Path | Purpose |
|---|---|
| `project.py` | Download, validation, analysis, and optional agent CLI |
| `run.cmd` | One-command environment setup, complete run, and browser report |
| `sql/group_metrics.sql` | Assigned-group conversion and revenue metrics |
| `sql/customer_segments.sql` | Exploratory recency breakdown |
| `docs/experiment_plan.md` | Metrics, comparisons, decision criteria, limitations |
| `docs/data_source.md` | Source, fields, and provenance rules |
| `data/raw/hillstrom.csv` | Unmodified published observations, excluded from Git |
| `data/raw/hillstrom.source.json` | Download URL, timestamp, SHA-256 |
| `data/processed/experiment.sqlite` | Rebuilt SQLite customer table; browse with any SQLite tool |
| `reports/results.json` | Machine-readable calculated evidence |
| `reports/group_metrics.csv` | SQL metrics, suitable for manual reconciliation |
| `reports/exploratory_recency.csv` | Descriptive subgroup results |
| `reports/conversion_lift.png` | Conversion effects and confidence intervals |
| `reports/dashboard.html` | Standalone visual report with purchases/revenue toggle and print support |
| `reports/runs/<timestamp>/dashboard.html` | A new dated report with stage statuses and this run's AI output |
| `reports/runs/<timestamp>/run.json` | Local/UTC timestamp, actual stage outcomes, and review assessment |
| `reports/index.html` | History of completed and failed run receipts, newest first |
| `reports/decision_report.md` | Deterministic report, usable without any AI API |
| `reports/agent_review.md` | DeepSeek's draft recommendation, when requested |
| `reports/agent_review.meta.json` | Evidence/draft hashes that prevent stale Jev reviews |
| `reports/jev_review.json` | Jev's structured advisory assessment and probabilities |
| `reports/review_status.json` | Whether the latest provider calls passed, failed, or remain incomplete |
| `tests/test_project.py` | Statistical, validation, SQL, and mocked agent checks |

`run.cmd` (or `project.py run`) creates isolated dated output folders. Individual `analyze`/`review` commands still rebuild their legacy report files. Do not store manual edits in generated files. The raw source is never overwritten by the download command. `customer_row_id` is a zero-based import row number, not an original customer ID. Rerunning unchanged data reproduces the numerical results; a new file is a new execution receipt, not new experimental evidence.

The downloader uses the scikit-uplift-documented HTTPS mirror because the publisher endpoint failed certificate validation during setup. It checks the documented compressed-file checksum before validating the CSV. See [source provenance](docs/data_source.md).

## Optional DeepSeek + Jev review

The analysis works fully offline once dependencies and data are downloaded. Running `review` is an explicit opt-in: it sends aggregate experiment evidence to DeepSeek through Token Harbor and, if `JEV_KEY` is configured, sends that evidence plus the generated draft to Jev. No source customer rows are sent. The selected Token Harbor model uses its free allowance; Jev requests use the configured TypeSafe account.

Put your existing keys in this project's local `.env`, using the names below. `.env` is excluded from Git. `.env.example` contains blank placeholders, never real keys.

```dotenv
DEEPSEEK_API_KEY=your-local-key
JEV_KEY=your-local-key
DEEPSEEK_MODEL=deepseek-v4.1-flash:free
JEV_MODEL=jev-latest
```

The review commands load only these four settings from the `.env` beside `project.py`. Existing terminal variables take precedence. Basic literal `KEY=value`, optional quotes, `export`, and trailing comments are supported. There is no variable interpolation, shell execution, or multiline support. Quote values containing spaces or `#`. Other variable names are ignored. Analysis/download commands do not load credentials. Neighboring key files are not read, and this project never modifies `.env`.

```powershell
# Generate a DeepSeek draft and then have Jev assess it:
.\.venv\Scripts\python.exe project.py review

# Reassess the current unchanged draft with Jev without another DeepSeek call:
.\.venv\Scripts\python.exe project.py jev-review
```

The model chooses from two read-only tools: `get_quality` and `get_comparison`. These return calculated evidence; the agent cannot execute arbitrary Python, SQL, shell commands, or file reads. It must retrieve the quality report and both comparisons before its draft is accepted. A run permits at most five API requests, four tool calls per response, and 1,800 output tokens per request. Network calls have explicit timeouts. The generated `reports/agent_review.md` is a draft requiring human verification; its numerical claims are not automatically certified.

The DeepSeek connection uses [Token Harbor's documented endpoint and model](https://tokenharbor.ai/models/deepseek-v4.1-flash:free): `https://tokenharbor.ai/v1/chat/completions` with `deepseek-v4.1-flash:free`. The key stored under `DEEPSEEK_API_KEY` must be your Token Harbor key. It is not sent to DeepSeek's own API. The endpoint is fixed to the chosen provider. The free model has allowance limits; no paid fallback is selected. Live connectivity is separate from mocked tests; see [verification](docs/verification.md).

Jev uses [TypeSafe's evaluation API](https://docs.typesafe.ai/api) with `jev-latest` and one Choice question: `SUPPORTED`, `NEEDS_REVISION`, or `INSUFFICIENT_EVIDENCE`. Its response type, label, probabilities, and confidence are validated before saving. The numerical decision rules remain in Python. Jev's confidence describes its model judgment; it is not an experiment confidence interval, a p-value, or permission to launch a campaign. All outcomes require human review, without an uncalibrated automatic approval threshold.

Each assessment includes source/results/draft hashes. Changing the evidence or draft requires regenerating the DeepSeek review. Check `review_status.json` before treating existing reports as current: a failed new run can leave older report files on disk. Neither a provider outage nor a malformed answer is converted into a favorable assessment. Evaluate review quality on manually labeled examples before claiming reliability.

## How to present this project

Start with the business decision, explain randomization and all-assigned-user denominators, then show effect sizes and uncertainty. Discuss missing costs and guardrails honestly. State that this is an independent retrospective analysis of a historical experiment, not a campaign you operated or revenue you generated.

The source has three arms: this project makes two A/B-style comparisons against the shared no-email control, accounting for both tests. It does not directly test the two email campaigns against each other. Segment exploration is descriptive, not proof of a targeting strategy.

Next learning steps: understand and reproduce the SQL yourself, explain percentage points vs relative lift, inspect the statistical assumptions, then write your own stakeholder recommendation. Keep the optional AI review separate from the deterministic results.

## Reliability checks

Every SQL group metric is reconciled against an independent Pandas aggregation. Malformed AI response objects fail with sanitized errors and preserve a failed run receipt. Existing source manifests are checked before analysis; manual sources without manifests are explicitly identified in the quality report. The Windows launcher uses the supplied dependency lock for first-time installation.
