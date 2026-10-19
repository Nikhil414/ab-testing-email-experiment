import re
import unittest

import project
from visual_report import render_dashboard
from test_project import fixture


class VisualReportTests(unittest.TestCase):
    def setUp(self):
        frame = fixture()
        self.results = {'quality': project.quality_report(frame),
                        'comparisons': [project.compare(frame, c) for c in project.CAMPAIGNS]}
        for row in self.results['comparisons']:
            row['positive_conversion_evidence'] = row['positive_conversion_evidence_before_quality_gate']
        self.metrics = []
        for name, group in frame.groupby('segment'):
            self.metrics.append({'segment': name, 'assigned_users': len(group),
                                 'purchases': int(group.conversion.sum()),
                                 'conversion_rate': float(group.conversion.mean()),
                                 'revenue_per_assigned_user': float(group.spend.mean())})

    def test_converts_percentage_points_to_per_thousand_and_includes_denominator(self):
        page = render_dashboard(self.results, self.metrics)
        self.assertIn('+100.0<small> / 1,000', page)
        self.assertIn('40 purchased / 200 assigned', page)
        self.assertIn('600 assigned customers', page)
        self.assertIn('20.00%', page)
        self.assertIn('id="revenue-panel"', page)
        self.assertNotIn('$conversion_bars', page)
        self.assertNotIn('Both emails increased purchases in this experiment.', page)

    def test_allocation_warning_blocks_positive_headline(self):
        self.results['quality']['allocation_warning'] = True
        for row in self.results['comparisons']:
            row['positive_conversion_evidence'] = True
        page = render_dashboard(self.results, self.metrics)
        self.assertIn('Resolve the allocation warning', page)
        self.assertNotIn('Positive historical evidence', page)

    def test_chart_positions_cover_negative_and_positive_intervals(self):
        self.results['comparisons'][0]['conversion_ci_percentage_points'] = [-15, 5]
        self.results['comparisons'][0]['absolute_lift_percentage_points'] = -5
        page = render_dashboard(self.results, self.metrics)
        self.assertIn('-50.0<small> / 1,000', page)
        positions = re.findall(r'(?:left|width):(-?[\d.]+)%', page)
        self.assertTrue(positions)
        self.assertTrue(all(0 <= float(value) <= 100 for value in positions))

    def test_standalone_report_has_no_remote_dependencies_or_credential_names(self):
        page = render_dashboard(self.results, self.metrics)
        self.assertNotRegex(page, r'(?:src|href)=["\']https?://')
        self.assertNotIn('DEEPSEEK_API_KEY', page)
        self.assertIn('aria-pressed="true"', page)
        self.assertIn('97.5%', page)


if __name__ == '__main__':
    unittest.main()
