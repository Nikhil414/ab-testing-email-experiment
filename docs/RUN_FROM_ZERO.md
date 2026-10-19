# One command, from setup to a visible result

## 1. Before your first run

Keep this project folder together, including `project.py`, `visual_report.py`, `templates`, `sql`, and both dependency requirement files. Install Python if it is not already available as `python` in PowerShell. The project was tested on Windows with Python 3.14.7.

Keep any existing local .env private. For a new clone, configure only the optional providers you intend to use.

For a fresh checkout, copy `.env.example` to `.env` and privately enter your Token Harbor key as `DEEPSEEK_API_KEY` and your TypeSafe key as `JEV_KEY`. Default models are `deepseek-v4.1-flash:free` and `jev-latest`. Keep `.env` out of Git. Existing terminal variables override its values. Missing AI keys do not prevent the numerical analysis.

## 2. Run this exact command

Open PowerShell in the cloned repository folder and run:

```powershell
.\run.cmd
```

Use the same command every time. You do not need to activate `.venv`, type `deactivate`, or change PowerShell execution policy. The command moves into the correct folder itself.

## 3. What happens, in order

1. **Environment:** create `.venv` if missing and install dependencies if their imports are unavailable. First-time setup needs Python and internet access; no machine-wide configuration is changed.
2. **Source data:** download the documented public dataset if absent, otherwise retain and validate the existing file.
3. **Analysis:** calculate the SQL metrics, validate/reconcile totals, calculate effect estimates and confidence intervals, and generate charts.
4. **DeepSeek:** if configured, send only public aggregate evidence through Token Harbor and generate a new draft recommendation. The selected free model uses its provider allowance; there is no paid fallback.
5. **Jev:** if configured and DeepSeek completes, assess that new draft against the evidence. TypeSafe requests use your account allowance or credits. `SUPPORTED` and `NEEDS_REVISION` are advisory labels, not statistical results or launch approvals.
6. **Your result:** create a new dated HTML page and open it in your default browser. The run receipt shows completed, skipped, and failed stages, plus this run's Jev assessment and an expandable AI draft when available.

## 4. What you receive every completed run

The outputs are saved under a new folder, for example:

```text
reports/
  index.html
  runs/
    2026-10-18_14-30-15_123456/
      dashboard.html
      run.json
      results.json
      group_metrics.csv
      exploratory_recency.csv
      decision_report.md
      conversion_lift.png
      agent_review.md          # only if DeepSeek completes
      agent_review.meta.json   # only if DeepSeek completes
      jev_review.json          # only if Jev completes
      review_status.json       # when AI review is attempted
```

The date, time, and microseconds make each run folder distinct. Older run folders are preserved. Open `reports/index.html` to revisit any saved run; each dated page also links back to that history.

The visual report answers: what happened to purchase conversion, how much extra purchasing/revenue is estimated, how uncertain those estimates are, and what the next business action should be. Switch between Purchases and Revenue.

Rerunning the same data gives the same statistical estimates. AI wording or assessments may vary. The visible reward is a newly recorded, inspectable run, not a claim that repeating an analysis improves the experiment.

## 5. If something fails

- If an AI provider fails, you still receive the completed numerical analysis with the failed stage clearly shown. An older AI draft is never substituted into a new run.
- If source validation or analysis fails, you receive a failure receipt without stale statistical charts. Previous saved runs remain available.
- A failure returns a nonzero command exit code even if a receipt was created. Missing optional keys are displayed as skipped stages.
- If browser opening is unavailable, open the new HTML path printed in the terminal or use `reports/index.html`.
- Failures before Python/dependencies are ready, unavailable disk space, and forcibly interrupted processes can prevent a receipt from being saved. Their errors remain in the terminal.

The dated outputs are local and excluded from Git by default, as are credentials. No campaign is sent or launched by running this command.
