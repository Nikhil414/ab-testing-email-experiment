# Verification

The deterministic analysis uses the public historical Hillstrom email experiment.
The source CSV, credentials, SQLite database, and dated AI receipts are excluded
from Git. Download the source before rerunning analysis.

The regression suite covers per-group SQL/Pandas reconciliation, statistical
calculations, data validation, bounded read-only AI tools, malformed provider
responses, and saved failure receipts. Run:

    .venv\Scripts\python.exe -m unittest discover -s tests -v

The supplied deterministic reports describe historical evidence. They do not
establish present-day effectiveness, campaign profitability, or an AI approval.
The final human-readable conclusion is in final_recommendation.md.

Verification of this revision: all 46 regression tests passed in memory against the prepared source, and the corrected per-group reconciliation passed on the 64,000-row local dataset. Statistical outputs were unchanged. Fresh installation and live provider calls were not tested for this revision.
