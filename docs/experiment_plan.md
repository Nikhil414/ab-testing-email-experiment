# Retrospective analysis plan

**Decision:** whether the historical retailer had evidence to prefer either email campaign to sending no email. This is a retrospective analysis of a published 2008 trial, not a newly run experiment or a preregistration.

**Population:** the source describes 64,000 customers who purchased within the preceding 12 months, randomly allocated approximately equally to Mens E-Mail, Womens E-Mail, or No E-Mail. The outcome window is the following two weeks.

**Unit:** one source row per assigned customer. There is no original customer identifier in the published columns. Import row numbers identify records only; they cannot establish cross-group contamination or unique real people.

**Primary outcome:** binary purchase conversion among all assigned customers. Planned comparisons: Mens E-Mail vs No E-Mail and Womens E-Mail vs No E-Mail. Two-sided alpha 0.05, with Bonferroni correction across these two comparisons (threshold 0.025 each). Report absolute lift in percentage points, relative lift, raw and adjusted p-values, and 97.5% individual confidence intervals that jointly have at least approximately 95% coverage under the normal approximation. Confidence intervals use unpooled standard errors; the two-proportion z-test uses the pooled null variance. Sparse outcomes stop the normal-approximation analysis.

**Secondary outcome:** revenue per assigned customer, including zero spend. Report mean differences and Welch t confidence intervals at 97.5% for each of the two contrasts. Revenue is skewed: treat these intervals as large-sample approximations and examine the distribution before making financial claims. These secondary intervals do not provide joint coverage across all primary and secondary outcomes together. No profit claim: email costs and margins are unavailable.

**Quality gates:** required columns, no missing/non-finite values, valid categories and binary outcomes, valid numeric ranges, conversion/visit/spend consistency, all three groups present, and an allocation check against equal thirds (warning threshold p < 0.001). An allocation warning blocks the positive-evidence flag pending investigation. Exact repeated rows are counted and retained because customer IDs are absent. Validate SQL/Python aggregate reconciliation.

**Decision rule:** flag positive conversion evidence only if adjusted p < 0.05, estimated lift is positive, and the allocation check passes. This flag is not a launch authorization or a claim of profitability. Review secondary revenue effects, missing guardrails, limitations, and stakeholder requirements. Failure to find significance does not establish equivalence. Negative significant effects are reported as adverse evidence.

**Unavailable checks:** email delivery, unsubscribe/complaint rates, cancellations, assignment logs, original stopping rules, and pre-experiment conversion baselines. Do not manufacture those fields or claim those checks passed. The published two-week window is fixed; do not repeatedly peek for a favorable result.

**Exploration:** recency segments are descriptive only. Any targeting policy needs independent validation. Do not choose a winner solely by comparing raw campaign conversion rates; a direct campaign-vs-campaign inference would require an additional planned comparison.

**Follow-up experiment:** choose a minimum worthwhile improvement, power, sample size, and stopping rule before collecting new data. A retrospective power calculation cannot prove the original experiment was well designed.
