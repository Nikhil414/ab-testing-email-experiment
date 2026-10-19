import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import project
from test_project import fixture


class RunTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.reports = Path(self.temp.name) / 'reports'
        self.reports.mkdir()
        for mocked in [patch.object(project, 'REPORTS', self.reports),
                       patch.object(project, 'download'),
                       patch.object(project, 'load_config'),
                       patch.object(project, 'analyze', side_effect=self.analysis),
                       patch.dict(os.environ, {}, clear=True)]:
            mocked.start()
            self.addCleanup(mocked.stop)

    def analysis(self):
        frame = fixture()
        comparisons = [project.compare(frame, c) for c in project.CAMPAIGNS]
        for row in comparisons:
            row['positive_conversion_evidence'] = row['positive_conversion_evidence_before_quality_gate']
        results = {'quality': project.quality_report(frame), 'comparisons': comparisons}
        metrics = []
        for name, group in frame.groupby('segment'):
            metrics.append({'segment': name, 'assigned_users': len(group),
                            'purchases': int(group.conversion.sum()),
                            'conversion_rate': float(group.conversion.mean()),
                            'revenue_per_assigned_user': float(group.spend.mean())})
        import pandas as pd
        project.write_json(project.REPORTS / 'results.json', results)
        project.write_text(project.REPORTS / 'group_metrics.csv', pd.DataFrame(metrics).to_csv(index=False))

    def manifests(self):
        return sorted(self.reports.glob('runs/*/run.json'))

    def test_every_run_preserves_older_results_and_history(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(project.run(open_browser=False), 0)
            first = self.manifests()[0]
            original = first.read_bytes()
            self.assertEqual(project.run(open_browser=False), 0)
        self.assertEqual(len(self.manifests()), 2)
        self.assertEqual(first.read_bytes(), original)
        self.assertEqual(project.REPORTS, self.reports)
        history = (self.reports / 'index.html').read_text()
        for manifest in self.manifests():
            self.assertIn(manifest.parent.name, history)
            report = (manifest.parent / 'dashboard.html').read_text()
            self.assertIn('Your analysis is ready', report)
            self.assertIn('AI review skipped', report)

    def test_data_failure_still_creates_receipt_without_stale_charts_or_secrets(self):
        project.write_text(self.reports / 'agent_review.md', 'OLD draft')
        with patch.object(project, 'download', side_effect=ValueError('sensitive-placeholder')), redirect_stdout(io.StringIO()):
            self.assertEqual(project.run(open_browser=False), 1)
        manifest = self.manifests()[0]
        saved = json.loads(manifest.read_text())
        page = (manifest.parent / 'dashboard.html').read_text()
        self.assertEqual(saved['stages']['data'], 'failed')
        self.assertIn('No statistical results are shown', page)
        self.assertNotIn('sensitive-placeholder', page)
        self.assertNotIn('OLD draft', page)

    def test_jev_failure_preserves_fresh_draft_and_shows_honest_status(self):
        os.environ.update(DEEPSEEK_API_KEY='placeholder', JEV_KEY='placeholder')

        def failed_review():
            project.write_text(project.REPORTS / 'agent_review.md', '<script>untrusted draft</script>')
            project.write_json(project.REPORTS / 'review_status.json', {'deepseek': 'passed', 'jev': 'failed'})
            raise ValueError('Jev returned HTTP 503; response body withheld.')

        with patch.object(project, 'review', side_effect=failed_review), redirect_stdout(io.StringIO()):
            self.assertEqual(project.run(open_browser=False), 1)
        manifest = self.manifests()[0]
        saved = json.loads(manifest.read_text())
        page = (manifest.parent / 'dashboard.html').read_text()
        self.assertEqual(saved['stages'], {'data': 'passed', 'analysis': 'passed',
                                          'deepseek': 'passed', 'jev': 'failed'})
        self.assertIn('HTTP 503', page)
        self.assertIn('&lt;script&gt;untrusted draft&lt;/script&gt;', page)
        self.assertNotIn('<script>untrusted draft</script>', page)

    def test_completed_run_saves_assessment_and_opens_its_own_report(self):
        os.environ.update(DEEPSEEK_API_KEY='placeholder', JEV_KEY='placeholder')

        def successful_review():
            project.write_text(project.REPORTS / 'agent_review.md', 'New draft')
            project.write_json(project.REPORTS / 'review_status.json', {'deepseek': 'passed', 'jev': 'passed'})
            project.write_json(project.REPORTS / 'jev_review.json', {'assessment': 'NEEDS_REVISION'})

        with patch.object(project, 'review', side_effect=successful_review), patch.object(
                project.webbrowser, 'open', return_value=True) as browser, redirect_stdout(io.StringIO()):
            self.assertEqual(project.run(), 0)
        manifest = self.manifests()[0]
        self.assertEqual(json.loads(manifest.read_text())['assessment'], 'NEEDS_REVISION')
        self.assertIn('Jev assessment: NEEDS_REVISION', (manifest.parent / 'dashboard.html').read_text())
        browser.assert_called_once_with((manifest.parent / 'dashboard.html').resolve().as_uri())

    def test_corrupt_history_does_not_prevent_new_report(self):
        project.write_text(self.reports / 'runs/old/run.json', 'invalid JSON')
        with redirect_stdout(io.StringIO()):
            self.assertEqual(project.run(open_browser=False), 0)
        self.assertTrue((self.reports / 'index.html').exists())
        self.assertIn('Your analysis is ready', (self.reports / 'index.html').read_text())

    def test_malformed_provider_message_saves_failed_receipt(self):
        os.environ['DEEPSEEK_API_KEY'] = 'placeholder'
        original = project.review_agent

        class MalformedResponse:
            ok = True
            def json(self):
                return {'choices': [{'finish_reason': 'stop', 'message': None}]}

        def malformed_review(*args):
            return original(*args, post=lambda *a, **k: MalformedResponse())

        with patch.object(project, 'load_current_results', return_value={}), patch.object(
                project, 'review_agent', side_effect=malformed_review), redirect_stdout(io.StringIO()):
            self.assertEqual(project.run(open_browser=False), 1)
        manifest = self.manifests()[0]
        saved = json.loads(manifest.read_text())
        page = (manifest.parent / 'dashboard.html').read_text()
        self.assertEqual(saved['stages']['analysis'], 'passed')
        self.assertEqual(saved['stages']['deepseek'], 'failed')
        self.assertEqual(saved['stages']['jev'], 'not_run')
        self.assertIn('AI review needs attention', page)
        self.assertFalse((manifest.parent / 'agent_review.md').exists())
        self.assertEqual(
            json.loads((manifest.parent / 'review_status.json').read_text()),
            {'deepseek': 'failed', 'jev': 'not_run'})

    def test_known_provider_failure_has_an_actionable_nonsecret_note(self):
        os.environ['DEEPSEEK_API_KEY'] = 'placeholder'
        with patch.object(project, 'review', side_effect=ValueError(
                'Agent response incomplete; no review saved.')), redirect_stdout(io.StringIO()):
            self.assertEqual(project.run(open_browser=False), 1)
        report = (self.manifests()[0].parent / 'dashboard.html').read_text()
        self.assertIn('AI draft exceeded its output limit or was interrupted', report)


if __name__ == '__main__':
    unittest.main()
