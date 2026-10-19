"""Render a standalone, offline results page from calculated evidence."""

from html import escape
from pathlib import Path
from string import Template


NAMES = {'No E-Mail': 'No email', 'Mens E-Mail': "Men's email", 'Womens E-Mail': "Women's email"}
COLORS = {'No E-Mail': 'control', 'Mens E-Mail': 'mens', 'Womens E-Mail': 'womens'}


def rate_chart(metrics, revenue=False):
    field = 'revenue_per_assigned_user' if revenue else 'conversion_rate'
    ceiling = max(float(r[field]) for r in metrics) * 1.15
    rows = []
    for row in metrics:
        name = row['segment']
        value = float(row[field])
        label = f'{value:.3f}' if revenue else f'{value:.2%}'
        detail = (f'{int(row["assigned_users"]):,} assigned customers' if revenue else
                  f'{int(row["purchases"]):,} purchased / {int(row["assigned_users"]):,} assigned')
        width = value / ceiling * 100 if ceiling else 0
        rows.append(f'<div class="bar-row"><div class="bar-label"><strong>{escape(NAMES[name])}</strong>'
                    f'<b>{label}</b></div><div class="bar-track"><span class="bar {COLORS[name]}" '
                    f'style="width:{width:.3f}%"></span></div><small>{detail}</small></div>')
    return ''.join(rows)


def interval_chart(comparisons, revenue=False):
    factor = 1 if revenue else 10  # percentage points to extra purchases per 1,000 assigned
    effect = 'revenue_difference_per_assigned_user' if revenue else 'absolute_lift_percentage_points'
    interval = 'revenue_difference_ci' if revenue else 'conversion_ci_percentage_points'
    lower = min(0, *(float(c[interval][0]) * factor for c in comparisons))
    upper = max(0, *(float(c[interval][1]) * factor for c in comparisons))
    padding = (upper - lower) * .12 or 1
    lower, upper = lower - padding, upper + padding

    def position(value):
        return (value - lower) / (upper - lower) * 100

    rows = []
    digits = 3 if revenue else 1
    for row in comparisons:
        value = float(row[effect]) * factor
        low, high = [float(v) * factor for v in row[interval]]
        name = row['campaign']
        rows.append(f'<div class="interval-row"><div class="bar-label"><strong>{escape(NAMES[name])}</strong>'
                    f'<b>{value:+.{digits}f}</b></div><div class="interval-track" aria-hidden="true">'
                    f'<span class="zero" style="left:{position(0):.3f}%"></span>'
                    f'<span class="range {COLORS[name]}" style="left:{position(low):.3f}%;'
                    f'width:{position(high)-position(low):.3f}%"></span>'
                    f'<span class="point {COLORS[name]}" style="left:{position(value):.3f}%"></span></div>'
                    f'<small>97.5% interval: {low:+.{digits}f} to {high:+.{digits}f}</small></div>')
    rows.append(f'<div class="axis" aria-hidden="true"><span>{lower:.{digits}f}</span>'
                f'<span>{upper:.{digits}f}</span></div>')
    return ''.join(rows)


def run_summary(info):
    """Render only explicitly recorded stages and this run's saved AI outputs."""
    labels = {'data': 'Source data', 'analysis': 'SQL + statistics',
              'deepseek': 'DeepSeek draft', 'jev': 'Jev review'}
    statuses = {'passed': 'Completed', 'failed': 'Failed', 'skipped': 'Skipped', 'not_run': 'Not run'}
    chips = ''.join(f'<li><strong>{label}</strong><span>{statuses.get(info["stages"][name], "Incomplete")}</span></li>'
                    for name, label in labels.items())
    note = ''.join(f'<p>{escape(str(message))}</p>' for message in info.get('notes', []))
    assessment = info.get('assessment')
    if assessment:
        note += (f'<p><strong>Jev assessment: {escape(assessment)}</strong> '
                 '&mdash; advisory review of the draft, not statistical confidence or approval to launch.</p>')
    draft = info.get('draft')
    if draft:
        note += ('<details><summary>Read this run\'s AI draft</summary><pre class="draft">'
                 + escape(draft) + '</pre></details>')
    return (f'<section class="run-receipt" aria-label="Run receipt"><p class="eyebrow">Your run receipt</p>'
            f'<h2>{escape(info["outcome"])}</h2><p>{escape(info["created_local"])}</p>'
            f'<ul>{chips}</ul>{note}<p>New report saved for this run. '
            '<a href="../../index.html">See all previous runs</a></p></section>')


def render_failed_run(info):
    return ('<!doctype html><html lang="en"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Experiment run needs attention</title><style>'
            'body{font:17px/1.6 Segoe UI,Arial,sans-serif;max-width:850px;margin:50px auto;padding:25px;'
            'background:#f2f5f1;color:#182b29}li{margin:15px 0}li span{margin-left:20px}'
            'a{color:#205e4d}pre{white-space:pre-wrap}</style><main>'
            + run_summary(info) + '<p>No statistical results are shown because this run did not complete '
            'the analysis. Previous reports remain in the run history.</p></main></html>')


def render_dashboard(results, metrics, run_info=None):
    quality = results['quality']
    comparisons = results['comparisons']
    positives = sum(bool(c['positive_conversion_evidence']) for c in comparisons)
    if quality['allocation_warning']:
        headline = 'Investigate the group allocation before drawing a conclusion.'
        verdict = 'Data check needs attention'
        tone = 'caution'
        decision = 'Resolve the allocation warning before recommending a rollout.'
        decision_detail = 'Investigate why the group counts differ from the expected allocation. '
        decision_detail += 'Resolve the issue before relying on the effect estimates.'
    elif positives == len(comparisons):
        headline = 'Both emails increased purchases in this experiment.'
        verdict = 'Positive historical evidence'
        tone = 'positive'
        decision = 'Run a fresh controlled experiment before a current rollout.'
        decision_detail = "The historical results are encouraging. Test again with today's customers and measure "
        decision_detail += 'costs, margins, cancellations, and unsubscribe or complaint rates.'
    else:
        headline = 'The evidence does not support a positive effect for every campaign.'
        verdict = 'Review the individual comparisons'
        tone = 'caution'
        decision = 'Do not roll out a campaign on these results alone.'
        decision_detail = 'Review each effect estimate and its uncertainty. Define the evidence and '
        decision_detail += 'business guardrails needed before a follow-up experiment.'
    cards = []
    for row in comparisons:
        lift = row['absolute_lift_percentage_points'] * 10
        cards.append(f'<article class="stat"><span>{escape(NAMES[row["campaign"]])} vs no email</span>'
                     f'<strong>{lift:+.1f}<small> / 1,000</small></strong>'
                     '<p>Estimated extra purchases per 1,000 assigned customers</p></article>')
    template = Template((Path(__file__).parent / 'templates/dashboard.html').read_text(encoding='utf-8'))
    return template.substitute(
        run_summary=run_summary(run_info) if run_info else '',
        tone=tone, verdict=escape(verdict), headline=escape(headline),
        decision=escape(decision), decision_detail=escape(decision_detail),
        customers=f'{quality["rows"]:,}', cards=''.join(cards),
        conversion_bars=rate_chart(metrics), revenue_bars=rate_chart(metrics, revenue=True),
        conversion_intervals=interval_chart(comparisons),
        revenue_intervals=interval_chart(comparisons, revenue=True),
        allocation_note=('Investigate the allocation warning before interpreting effects.'
                         if quality['allocation_warning'] else
                         'No allocation imbalance warning. SQL and Python totals reconcile.'),
        repeated_rows=f'{quality["repeated_complete_rows_retained"]:,}',
    )
