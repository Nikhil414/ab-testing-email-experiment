# Project recommendation: Which Campaign Actually Creates More Sales?

Build an end-to-end experiment analysis that answers: **Should a retailer send campaign A, campaign B, or no campaign—and what evidence supports that decision?**

This is my strongest recommendation for your current A/B testing focus. It combines a real business problem, published randomized experiment data, statistics, and a recommendation that a business stakeholder can use.

## The real problem

Customers may buy after receiving a marketing email even when the email did not influence their decision. Counting every purchase after a campaign can overstate its value. Your project estimates the extra purchases and revenue caused by assigning customers to receive a campaign.

The final result should explain which campaign to use, how uncertain the estimated benefit is, and whether more evidence is needed. A valid conclusion can be “the evidence is inconclusive.”

## Use a real experiment

Start with the **Hillstrom / MineThatData Email Analytics Challenge**. Its publisher describes 64,000 customers randomly divided into three groups: a men's merchandise email, a women's merchandise email, and no email. Outcomes were tracked for two weeks. The data includes historical customer attributes and subsequent visits, purchases, and spending.

Source: [Original dataset description and download link](https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html).

This is a historical 2008 experiment. Present it as a retrospective case study, not evidence of current consumer behavior. The publisher's description was checked; the actual data download and file contents have not yet been verified.

## What to build

| Part | Work | Evidence for a reviewer |
|---|---|---|
| Business brief | Define the decision, eligible population, primary metric, and comparison plan | A one-page analysis plan |
| SQL analysis | Load the source data; validate fields; calculate outcomes by assigned group | Readable SQL with reconciled counts and totals |
| Data quality | Check missing values, valid treatment labels, binary outcomes, group counts, and suspicious repeated records | A short quality report explaining unresolved issues |
| Python statistics | Estimate absolute and relative conversion lift, revenue differences, and confidence intervals | A reproducible notebook or script |
| Excel review | Independently reconcile group counts, conversion rates, and spending totals | A compact calculation workbook |
| Power BI | Show experiment health, estimated effects, uncertainty, and the business recommendation | A focused results dashboard |
| Decision memo | Explain whether to adopt a campaign, keep the control, or run another test | A one-page stakeholder recommendation |

Use **SQL + Python + Excel + Power BI**. Start with the database you already know. An app, cloud deployment, AI agent, or machine-learning model is unnecessary for the first version.

## Questions your analysis should answer

1. Does either campaign increase purchases compared with no email?
2. How large is the increase in percentage points, and what is its confidence interval?
3. Does spending per assigned customer increase too?
4. Are the findings strong enough to support a decision?
5. What would the estimated financial benefit be under clearly stated campaign-cost and margin assumptions?

Use purchase conversion as the primary metric and spending per assigned customer as a secondary business outcome. Do not calculate the campaign's success using only people who opened, visited, or purchased: those actions occur after assignment and can bias the comparison.

Choose the planned comparisons before exploring results and account for testing multiple campaigns. Analyze the supplied assignment; do not invent a new random split of existing outcomes. Check the observed group proportions against the documented allocation, while noting that the public description rounds each group to one-third. Investigate repeated records rather than automatically deleting them: different customers may share identical recorded attributes.

Because this is an existing experiment, a written analysis plan is retrospective. A prospective sample-size calculation can be a separate exercise for a proposed follow-up experiment; it must not be presented as the original experiment's plan.

## What makes it interesting

Add a small **break-even scenario analysis**: under an assumed contribution margin and cost per email, how much incremental spending would justify the campaign? Keep assumptions visible and separate from measured results. Revenue is not profit, and this dataset alone cannot establish actual campaign profit.

After the core analysis works, explore whether effects vary by pre-existing customer characteristics such as purchase recency. Label these findings exploratory. Validate any targeting rule on held-out data before claiming that it improves decisions.

## How it fits different roles

No single project fits every job description or guarantees selection. This project gives you reusable evidence for several analytics roles; tailor which evidence you emphasize.

| Target role | Emphasize |
|---|---|
| Data Analyst | SQL, data validation, statistical analysis, clear findings |
| Business Analyst | Business problem, decision criteria, assumptions, stakeholder recommendation |
| BI Analyst / Developer | Metric definitions, data model, DAX, reconciliations, dashboard usability |
| Product / Growth Analyst | Randomized assignment, experiment validity, conversion lift, uncertainty |
| Marketing Analyst | Incremental campaign effect, audience analysis, spending outcomes |
| Analytics Engineer | Reproducible transformations, data grain, documented lineage, meaningful data checks |

For finance, supply-chain, or risk roles, a second domain-specific project will usually provide stronger evidence than forcing this experiment to cover those domains. Adapt the presentation to a job description without claiming tools, experience, or results you have not demonstrated.

As an example of overlapping skills, an Amazon Business Intelligence Engineer listing reviewed for this recommendation asks for SQL, Python, visualization, data modeling, and business-facing analytical work. That supports the stack choice; it does not establish that this project satisfies every employer's requirements. [Amazon role description](https://www.amazon.jobs/en/jobs/10579386/business-intelligence-engineer-consumables-insights-and-analytics).

## Two other good options

| Project | Business decision | Data approach and limitation |
|---|---|---|
| Simplified Checkout A/B Test | Should a retailer launch a shorter checkout? | Use explicitly labeled simulated assignments, events, and orders unless you obtain a real randomized checkout experiment. Measure conversion and revenue per assigned user, with cancellation guardrails. |
| Advertising Incrementality Study | Does advertising cause extra conversions? | Use Criteo's published randomized incrementality-test dataset. Review its version, documentation, and permitted uses before implementation; its anonymized features limit business interpretation. |

The checkout option is useful for practicing event joins and experiment design. The email experiment is my first choice for a manageable case study using documented real randomization. Criteo is an optional larger-data follow-up. [Criteo dataset documentation](https://ailab.criteo.com/criteo-uplift-prediction-dataset/).

## Smallest complete version

Finish one clean SQL analysis, one reproducible statistical analysis, one Excel reconciliation, one Power BI report, and one decision memo. Publish a README covering the question, source, methods, findings, limitations, and reproduction steps.

A truthful resume description after completion could be:

> Analyzed a published randomized email experiment using SQL and Python, reconciled results in Excel, and built a Power BI report estimating incremental conversion and revenue with confidence intervals.

Only add numerical results after calculating and validating them. Describe historical case-study findings as estimates; do not claim that you generated revenue or ran the original experiment.
