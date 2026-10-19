# Data source and provenance

Publisher: Kevin Hillstrom, MineThatData, 2008 Email Analytics Challenge.

- Description: https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html
- CSV: https://www.minethatdata.com/Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv
- Download mirror: https://hillstorm1.s3.us-east-2.amazonaws.com/hillstorm_no_indices.csv.gz
- Mirror provenance and compressed-file MD5: https://www.uplift-modeling.com/en/latest/_modules/sklift/datasets/datasets.html (the `fetch_hillstrom` implementation).

The publisher HTTPS endpoint failed certificate validation during setup. `python project.py download` uses the HTTPS mirror documented by scikit-uplift, checks its published compressed-file MD5 for accidental changes, decompresses the CSV, validates its schema and 64,000-row count, and writes a SHA-256/source manifest. It does not contact DeepSeek. Data is excluded from Git by default. Public availability does not establish an unrestricted redistribution license: link to the publisher instead of republishing the raw data without checking permission.

Source columns:

| Column | Meaning |
|---|---|
| recency | Months since prior purchase |
| history_segment | Historical spending category |
| history | Prior-year spending |
| mens / womens | Prior merchandise purchase indicators |
| zip_code | Urban, Suburban, or Rural classification |
| newbie | New customer indicator |
| channel | Historical channel: Phone, Web, or Multichannel |
| segment | Randomized email assignment |
| visit | Visited during the outcome window |
| conversion | Purchased during the outcome window |
| spend | Spending during the outcome window, including zeros |

The published CSV spells the suburban category `Surburban`. It is accepted and retained verbatim; do not interpret it as a fourth geographic category.

The importer adds `customer_row_id`, a sequential record number. It is not an original customer identifier. Whole-row duplicates are retained and reported, not silently dropped. No extra demographic, cost, cancellation, or email-open variables are invented.

Raw data remains unchanged. SQLite and reports are reproducible derived files. If the publisher download is unavailable, obtain the same published CSV through a permitted route, place it at `data/raw/hillstrom.csv`, then run `analyze`. The analysis manifest records the actual file hash even for a manual download. Never substitute synthetic data without clearly changing its provenance and claims.

Existing files must have 64,000 rows. If a source manifest exists, its SHA-256 must match before analysis proceeds. Manually supplied files without a manifest are explicitly marked as having unverified source identity in the quality report.
