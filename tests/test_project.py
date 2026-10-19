import io
from contextlib import closing, redirect_stdout
import json
import math
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import tempfile

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import project


def fixture():
    rows = []
    for group, purchases in [(project.CONTROL, 20), (project.CAMPAIGNS[0], 40),
                             (project.CAMPAIGNS[1], 20)]:
        for i in range(200):
            bought = int(i < purchases)
            rows.append(dict(recency=3, history=120.0, mens=1, womens=0, newbie=0,
                             visit=bought, conversion=bought, spend=bought * 20.0,
                             history_segment='2) $100 - $200', zip_code='Urban',
                             channel='Web', segment=group))
    return pd.DataFrame(rows)


def load(frame):
    return project.load_data(io.StringIO(frame.to_csv(index=False)))


class AnalysisTests(unittest.TestCase):
    def test_valid_data_preserves_repeated_rows(self):
        frame = load(fixture())
        self.assertEqual(len(frame), 600)
        quality = project.quality_report(frame)
        self.assertGreater(quality['repeated_complete_rows_retained'], 0)
        self.assertFalse(quality['allocation_warning'])

    def test_rejects_invalid_outcomes_and_missing_data(self):
        for field, value in [('conversion', 2), ('spend', -1), ('history', float('inf')),
                             ('visit', None), ('recency', 13), ('segment', 'Unknown')]:
            with self.subTest(field=field):
                frame = fixture()
                frame.loc[0, field] = value
                with self.assertRaises(ValueError):
                    load(frame)

    def test_rejects_purchase_without_visit(self):
        frame = fixture()
        frame.loc[0, 'visit'] = 0
        with self.assertRaises(ValueError):
            load(frame)

    def test_source_suburban_spelling_preserved(self):
        frame = fixture()
        frame.loc[0, 'zip_code'] = 'Surburban'
        self.assertEqual(load(frame).loc[0, 'zip_code'], 'Surburban')

    def test_download_checksum_failure_does_not_save_source(self):
        class InvalidDownload:
            content = b'not-the-documented-source'

            def raise_for_status(self):
                pass

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'source.csv'
            with patch.object(project, 'RAW', path), patch.object(
                    project.requests, 'get', return_value=InvalidDownload()):
                with self.assertRaisesRegex(ValueError, 'checksum'):
                    project.download()
            self.assertFalse(path.exists())

    def test_existing_source_manifest_mismatch_is_rejected(self):
        frame = fixture()
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'hillstrom.csv'
            source.write_text(frame.to_csv(index=False), encoding='utf-8')
            project.write_json(source.with_suffix('.source.json'), {'sha256': 'different'})
            with patch.object(project, 'RAW', source), patch.object(project, 'load_data') as read:
                read.return_value = pd.concat([frame.iloc[:1]] * 64000, ignore_index=True)
                with self.assertRaisesRegex(ValueError, 'provenance manifest'):
                    project.download()

    def test_source_requires_published_row_count(self):
        with patch.object(project, 'load_data', return_value=fixture()):
            with self.assertRaisesRegex(ValueError, '64,000'):
                project.load_source()

    def test_matching_manifest_and_manual_source_are_accepted(self):
        import hashlib
        frame = pd.concat([fixture().iloc[:1]] * 64000, ignore_index=True)
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'hillstrom.csv'
            source.write_text('source bytes for hash test', encoding='utf-8')
            with patch.object(project, 'RAW', source), patch.object(project, 'load_data', return_value=frame):
                self.assertIs(project.load_source(), frame)
                project.write_json(source.with_suffix('.source.json'),
                                   {'sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
                self.assertIs(project.load_source(), frame)

    def test_missing_group_rejected(self):
        frame = fixture()
        with self.assertRaises(ValueError):
            load(frame[frame.segment != project.CAMPAIGNS[1]])

    def test_known_conversion_effect_and_correction(self):
        row = project.compare(fixture(), project.CAMPAIGNS[0])
        self.assertAlmostEqual(row['absolute_lift_percentage_points'], 10.0)
        self.assertAlmostEqual(row['relative_lift_percent'], 100.0)
        self.assertAlmostEqual(row['revenue_difference_per_assigned_user'], 2.0)
        # Independent numeric reference: p=2*(1-Phi(0.1/sqrt(.15*.85*.01))).
        self.assertAlmostEqual(row['raw_p_value'], 0.005101399646, places=10)
        self.assertAlmostEqual(row['bonferroni_adjusted_p_value'], 2 * row['raw_p_value'])
        self.assertGreater(row['conversion_ci_percentage_points'][0], 0)

    def test_identical_arms_do_not_show_positive_evidence(self):
        row = project.compare(fixture(), project.CAMPAIGNS[1])
        self.assertEqual(row['raw_p_value'], 1.0)
        self.assertEqual(row['absolute_lift_percentage_points'], 0)
        self.assertFalse(row['positive_conversion_evidence_before_quality_gate'])

    def test_sparse_outcomes_stop_normal_approximation(self):
        frame = fixture()
        frame.loc[frame.segment == project.CONTROL, 'conversion'] = 0
        with self.assertRaises(ValueError):
            project.compare(frame, project.CAMPAIGNS[0])

    def test_allocation_warning(self):
        frame = fixture()
        extra = frame[frame.segment == project.CONTROL]
        quality = project.quality_report(pd.concat([frame, extra, extra]))
        self.assertTrue(quality['allocation_warning'])

    def test_reconciliation_accepts_independent_group_metrics(self):
        import sqlite3
        frame = fixture()
        with closing(sqlite3.connect(':memory:')) as connection:
            frame.to_sql('customers', connection, index=False)
            metrics = pd.read_sql_query(
                (project.ROOT / 'sql/group_metrics.sql').read_text(), connection)
        project.reconcile_metrics(frame, metrics)

    def test_reconciliation_rejects_offsetting_errors_in_every_metric(self):
        import sqlite3
        frame = fixture()
        with closing(sqlite3.connect(':memory:')) as connection:
            frame.to_sql('customers', connection, index=False)
            metrics = pd.read_sql_query(
                (project.ROOT / 'sql/group_metrics.sql').read_text(), connection)
        for field in metrics.columns.drop('segment'):
            with self.subTest(field=field):
                changed = metrics.copy()
                changed.loc[0, field] += 1
                changed.loc[1, field] -= 1
                with self.assertRaisesRegex(ValueError, 'per-group reconciliation'):
                    project.reconcile_metrics(frame, changed)

    def test_reconciliation_rejects_missing_or_duplicated_groups(self):
        import sqlite3
        frame = fixture()
        with closing(sqlite3.connect(':memory:')) as connection:
            frame.to_sql('customers', connection, index=False)
            metrics = pd.read_sql_query(
                (project.ROOT / 'sql/group_metrics.sql').read_text(), connection)
        for changed in (metrics.iloc[:-1], pd.concat([metrics, metrics.iloc[:1]])):
            with self.assertRaisesRegex(ValueError, 'per-group reconciliation'):
                project.reconcile_metrics(frame, changed)

    def test_sql_matches_known_counts(self):
        import sqlite3
        with closing(sqlite3.connect(':memory:')) as connection:
            fixture().to_sql('customers', connection, index=False)
            rows = pd.read_sql_query((project.ROOT / 'sql/group_metrics.sql').read_text(), connection)
        self.assertEqual(rows.assigned_users.sum(), 600)
        self.assertEqual(rows.purchases.sum(), 80)
        self.assertTrue(math.isclose(rows.total_revenue.sum(), 1600))


class Response:
    ok = True

    def __init__(self, message, finish='stop'):
        self.message = message
        self.finish = finish

    def json(self):
        return {'choices': [{'message': self.message, 'finish_reason': self.finish}]}


class AgentTests(unittest.TestCase):
    def setUp(self):
        frame = fixture()
        self.results = {'quality': project.quality_report(frame),
                        'comparisons': [project.compare(frame, c) for c in project.CAMPAIGNS]}

    def test_only_allowlisted_tools(self):
        for name, args in [('execute_sql', {}), ('get_quality', {'path': 'secret'}),
                           ('get_comparison', {'campaign': 'Unknown'})]:
            with self.assertRaises(ValueError):
                project.tool_result(name, args, self.results)

    def test_agent_fetches_all_evidence_before_report(self):
        calls = [dict(id='quality', type='function',
                      function={'name': 'get_quality', 'arguments': '{}'})]
        for i, campaign in enumerate(project.CAMPAIGNS):
            calls.append(dict(id=str(i), type='function', function={
                'name': 'get_comparison', 'arguments': json.dumps({'campaign': campaign})}))
        responses = iter([Response({'role': 'assistant', 'content': None, 'tool_calls': calls}, 'tool_calls'),
                          Response({'role': 'assistant', 'content': 'Draft for human review.'})])
        requests_seen = []

        def fake_post(url, **kwargs):
            self.assertEqual(url, 'https://tokenharbor.ai/v1/chat/completions')
            requests_seen.append(json.loads(json.dumps(kwargs['json'])))
            return next(responses)

        report = project.review_agent(self.results, 'test-placeholder', 'test-model', post=fake_post)
        self.assertEqual(report, 'Draft for human review.')
        self.assertEqual(len(requests_seen), 2)
        evidence = [m for m in requests_seen[1]['messages'] if m['role'] == 'tool']
        self.assertEqual(len(evidence), 3)
        self.assertNotIn('test-placeholder', json.dumps(requests_seen))

    def test_malformed_provider_objects_fail_with_sanitized_value_error(self):
        bodies = [
            None, [], {'choices': 'private-placeholder'}, {'choices': []},
            {'choices': [None]},
            {'choices': [{'finish_reason': 'stop', 'message': None}]},
            {'choices': [{'finish_reason': 'stop', 'message': []}]},
            {'choices': [{'finish_reason': 'tool_calls', 'message': {'tool_calls': None}}]},
            {'choices': [{'finish_reason': 'tool_calls', 'message': {'tool_calls': [None]}}]},
            {'choices': [{'finish_reason': 'tool_calls', 'message': {'tool_calls': [
                {'id': 'q', 'function': None}]}}]},
            {'choices': [{'finish_reason': 'tool_calls', 'message': {'tool_calls': [
                {'id': 'q', 'function': {'name': 'get_quality', 'arguments': {}}}]}}]},
        ]
        class MalformedResponse:
            ok = True
            def json(self):
                return body
        for body in bodies:
            with self.subTest(shape=type(body).__name__):
                with self.assertRaises(ValueError) as raised:
                    project.review_agent(
                        self.results, 'private-placeholder', 'test-model',
                        post=lambda *args, **kwargs: MalformedResponse())
                self.assertNotIn('private-placeholder', str(raised.exception))

    def test_nontext_draft_is_rejected_after_fetching_evidence(self):
        calls = [dict(id='quality', function={'name': 'get_quality', 'arguments': '{}'})]
        calls += [dict(id=str(i), function={'name': 'get_comparison',
                  'arguments': json.dumps({'campaign': campaign})})
                  for i, campaign in enumerate(project.CAMPAIGNS)]
        for content in ({'claim': 'private-placeholder'}, ['private-placeholder'], '   '):
            responses = iter([
                Response({'content': None, 'tool_calls': calls}, 'tool_calls'),
                Response({'content': content})])
            with self.assertRaisesRegex(ValueError, 'did not fetch all evidence'):
                project.review_agent(self.results, 'placeholder', 'test-model',
                                     post=lambda *a, **k: next(responses))

    def test_premature_report_rejected(self):
        with self.assertRaises(ValueError):
            project.review_agent(self.results, 'test-placeholder', 'test-model',
                                 post=lambda *a, **k: Response({'content': 'Unsupported claim.'}))

    def test_request_budget(self):
        calls = [dict(id='q', type='function', function={'name': 'get_quality', 'arguments': '{}'})]
        seen = []

        def fake_post(*args, **kwargs):
            seen.append(1)
            return Response({'content': None, 'tool_calls': calls}, 'tool_calls')

        with self.assertRaises(ValueError):
            project.review_agent(self.results, 'test-placeholder', 'test-model', post=fake_post)
        self.assertEqual(len(seen), 5)


class ConfigTests(unittest.TestCase):
    def test_local_config_quotes_comments_and_terminal_precedence(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {}, clear=True):
            path = Path(folder) / '.env'
            path.write_text('\ufeffDEEPSEEK_API_KEY="placeholder-one" # comment\n'
                            "export JEV_KEY='placeholder-two'\nDEEPSEEK_MODEL=from-file\n"
                            'UNRELATED_SETTING=ignored\n', encoding='utf-8')
            os.environ['DEEPSEEK_MODEL'] = 'from-terminal'
            project.load_config(path)
            self.assertEqual(os.environ['DEEPSEEK_API_KEY'], 'placeholder-one')
            self.assertEqual(os.environ['JEV_KEY'], 'placeholder-two')
            self.assertEqual(os.environ['DEEPSEEK_MODEL'], 'from-terminal')
            self.assertNotIn('UNRELATED_SETTING', os.environ)

    def test_config_does_not_execute_or_expand_values(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {}, clear=True):
            path = Path(folder) / '.env'
            path.write_text('JEV_KEY="${OTHER_KEY}"\n', encoding='utf-8')
            project.load_config(path)
            self.assertEqual(os.environ['JEV_KEY'], '${OTHER_KEY}')

    def test_bad_config_error_withholds_value(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / '.env'
            path.write_text('JEV_KEY="placeholder-unclosed\n', encoding='utf-8')
            with self.assertRaises(ValueError) as raised:
                project.load_config(path)
            self.assertNotIn('placeholder-unclosed', str(raised.exception))

    def test_missing_config_is_optional(self):
        with tempfile.TemporaryDirectory() as folder:
            project.load_config(Path(folder) / 'missing.env')


class JevResponse:
    ok = True

    def __init__(self, body):
        self.body = body

    def json(self):
        return self.body


class JevTests(unittest.TestCase):
    def setUp(self):
        frame = fixture()
        self.results = {'quality': project.quality_report(frame),
                        'comparisons': [project.compare(frame, c) for c in project.CAMPAIGNS]}
        self.answer = {'type': 'choice', 'choice': 'SUPPORTED', 'confidence': 0.8,
                       'probabilities': {'SUPPORTED': 0.8, 'NEEDS_REVISION': 0.15,
                                         'INSUFFICIENT_EVIDENCE': 0.05}}

    def test_typed_advisory_and_aggregate_only_payload(self):
        seen = []

        def fake_post(url, **kwargs):
            seen.append(kwargs['json'])
            self.assertEqual(url, 'https://api.typesafe.ai/v1/systemone')
            return JevResponse({'answers': {'evidence_support': self.answer}})

        result = project.assess_with_jev(self.results, 'A historical draft.',
                                         'placeholder-key', post=fake_post)
        self.assertEqual(result['assessment'], 'SUPPORTED')
        self.assertTrue(result['human_review_required'])
        self.assertEqual(len(seen), 1)
        self.assertEqual(set(seen[0]['state']), {'evidence', 'draft_recommendation'})
        self.assertNotIn('placeholder-key', json.dumps(seen))

    def test_invalid_probability_outputs_rejected(self):
        bad_answers = [
            {**self.answer, 'choice': 'LAUNCH'},
            {**self.answer, 'confidence': float('nan')},
            {**self.answer, 'confidence': True},
            {**self.answer, 'probabilities': {'SUPPORTED': 0.9}},
            {**self.answer, 'probabilities': {'SUPPORTED': 0.8, 'NEEDS_REVISION': 0.8,
                                             'INSUFFICIENT_EVIDENCE': 0.8}},
            {**self.answer, 'choice': 'NEEDS_REVISION'},
        ]
        for answer in bad_answers:
            with self.subTest(answer=answer), self.assertRaises(ValueError):
                project.assess_with_jev(self.results, 'Draft.', 'placeholder-key',
                    post=lambda *a, **k: JevResponse({'answers': {'evidence_support': answer}}))

    def test_missing_answer_withheld(self):
        with self.assertRaisesRegex(ValueError, 'response body withheld'):
            project.assess_with_jev(self.results, 'Draft.', 'placeholder-key',
                                   post=lambda *a, **k: JevResponse({'unexpected': 'private response'}))

    def test_http_failure_does_not_read_body(self):
        class Denied:
            ok = False
            status_code = 401

            def json(self):
                raise AssertionError('Error response body must not be read.')

        with self.assertRaisesRegex(ValueError, 'HTTP 401'):
            project.assess_with_jev(self.results, 'Draft.', 'placeholder-key',
                                   post=lambda *a, **k: Denied())

    def test_changed_draft_rejected_before_jev_request(self):
        import hashlib
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'JEV_KEY': 'placeholder-key'}):
            reports = Path(folder)
            project.write_text(reports / 'results.json', '{}')
            project.write_text(reports / 'agent_review.md', 'Edited draft')
            project.write_json(reports / 'agent_review.meta.json', {
                'source_sha256': 'source',
                'results_sha256': hashlib.sha256((reports / 'results.json').read_bytes()).hexdigest(),
                'draft_sha256': hashlib.sha256(b'Original draft').hexdigest(),
            })
            with patch.object(project, 'REPORTS', reports), patch.object(
                    project, 'load_current_results', return_value={'source_sha256': 'source'}), patch.object(
                    project, 'assess_with_jev') as assess:
                with self.assertRaisesRegex(ValueError, 'Draft or evidence changed'):
                    project.jev_review()
                assess.assert_not_called()


class ReviewWorkflowTests(unittest.TestCase):
    def test_both_providers_run_and_save_evidence_hashes(self):
        results = {'source_sha256': 'fixture-source'}
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {
                'DEEPSEEK_API_KEY': 'placeholder-deepseek', 'JEV_KEY': 'placeholder-jev'}, clear=True):
            reports = Path(folder)
            project.write_json(reports / 'results.json', results)
            with patch.object(project, 'REPORTS', reports), patch.object(
                    project, 'load_current_results', return_value=results), patch.object(
                    project, 'review_agent', return_value='A historical draft.') as deepseek, patch.object(
                    project, 'assess_with_jev', return_value={
                        'assessment': 'SUPPORTED', 'human_review_required': True}) as jev, redirect_stdout(io.StringIO()):
                project.review()
            deepseek.assert_called_once()
            self.assertEqual(deepseek.call_args.args[2], 'deepseek-v4.1-flash:free')
            jev.assert_called_once()
            assessment = json.loads((reports / 'jev_review.json').read_text())
            metadata = json.loads((reports / 'agent_review.meta.json').read_text())
            self.assertEqual(assessment['draft_sha256'], metadata['draft_sha256'])
            self.assertEqual(json.loads((reports / 'review_status.json').read_text()),
                             {'deepseek': 'passed', 'jev': 'passed'})
            self.assertNotIn('placeholder-deepseek', (reports / 'agent_review.md').read_text())

    def test_jev_failure_preserves_draft_without_favorable_status(self):
        results = {'source_sha256': 'fixture-source'}
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {
                'DEEPSEEK_API_KEY': 'placeholder-deepseek', 'JEV_KEY': 'placeholder-jev'}, clear=True):
            reports = Path(folder)
            project.write_json(reports / 'results.json', results)
            with patch.object(project, 'REPORTS', reports), patch.object(
                    project, 'load_current_results', return_value=results), patch.object(
                    project, 'review_agent', return_value='A historical draft.'), patch.object(
                    project, 'assess_with_jev', side_effect=ValueError('Provider denied')), redirect_stdout(io.StringIO()):
                with self.assertRaises(ValueError):
                    project.review()
            self.assertTrue((reports / 'agent_review.md').exists())
            self.assertFalse((reports / 'jev_review.json').exists())
            self.assertEqual(json.loads((reports / 'review_status.json').read_text()),
                             {'deepseek': 'passed', 'jev': 'failed'})

    def test_deepseek_failure_does_not_call_jev(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {
                'DEEPSEEK_API_KEY': 'placeholder-deepseek', 'JEV_KEY': 'placeholder-jev'}, clear=True):
            reports = Path(folder)
            with patch.object(project, 'REPORTS', reports), patch.object(
                    project, 'load_current_results', return_value={}), patch.object(
                    project, 'review_agent', side_effect=ValueError('Provider denied')), patch.object(
                    project, 'assess_with_jev') as jev:
                with self.assertRaises(ValueError):
                    project.review()
                jev.assert_not_called()
            self.assertEqual(json.loads((reports / 'review_status.json').read_text()),
                             {'deepseek': 'failed', 'jev': 'not_run'})


if __name__ == '__main__':
    unittest.main()
