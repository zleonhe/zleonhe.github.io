"""Checks for data-loss and identity failures in the publication pipeline."""
import contextlib
import copy
import io
import unittest

from pybtex.database import Person

import publications as p

class PublicationsTests(unittest.TestCase):
    def record(self, **changes):
        item = {'type': 'article', 'key': 'he2026test', 'title': '{EDA}: A Paper',
                'author': [Person('He, Zhuolun'), Person('Yu, Bei')], 'journal': 'Journal',
                'year': '2026', 'sortkey': '0010', 'usera': 'stable-anchor'}
        item.update(changes)
        return item

    def test_nested_braces_quotes_and_escaped_ampersand(self):
        records = p.read_bib('@article{k, title={{EDA}: A {Nested} Title}, author="He, Zhuolun", year=2026, journal={A \\& B}}')
        self.assertEqual(p.plain(records[0]['title']), 'EDA: A Nested Title')
        self.assertEqual(p.plain(records[0]['journal']), 'A & B')
        self.assertEqual(p.author_names(records[0]['author']), ['Zhuolun He'])

    def test_institutional_author_keeps_its_boundary(self):
        entries = p.read_bib('@article{k, author={{Research and Development and QA Team} and He, Zhuolun}}')
        self.assertEqual(p.author_names(entries[0]['author']),
                         ['Research and Development and QA Team', 'Zhuolun He'])

    def test_duplicate_identifiers_fail_instead_of_skipping(self):
        first = self.record(doi='10.123/example')
        for field in ['key', 'usera', 'sortkey', 'doi']:
            second = self.record(key='other', usera='other', sortkey='0020', doi='10.123/other')
            second[field] = first[field]
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'Duplicate'):
                p.generate([first, second])

    def test_conference_and_journal_versions_survive(self):
        second = self.record(key='conference', usera='conference', sortkey='0020',
                             type='inproceedings', booktitle='Conference')
        with contextlib.redirect_stderr(io.StringIO()):
            output = p.generate([self.record(), second])
        self.assertEqual(len(output), 2)
        self.assertEqual({x['id'] for x in output}, {'stable-anchor', 'conference'})

    def test_resources_names_and_notes_survive(self):
        output = p.generate([self.record(doi='10.123/test', note="Editor's Pick",
            paper='https://example.org/paper.pdf', code='https://example.org/code')])[0]
        self.assertEqual(output['authors'], ['Zhuolun He', 'Bei Yu'])
        self.assertEqual(output['note'], "Editor's Pick")
        self.assertEqual(output['titleUrl'], 'https://doi.org/10.123/test')
        self.assertEqual(output['links'], [{'label':'Paper','url':'https://example.org/paper.pdf'},
                                          {'label':'Code','url':'https://example.org/code'}])

    def test_date_conflict_missing_metadata_and_dead_local_link_fail(self):
        for changes in [{'eventdate':'2025-06-01'}, {'author':''}, {'paper':'/pdf/missing-test-file.pdf'}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                p.generate([self.record(**changes)])

    def test_sorting_does_not_renumber_anchors(self):
        records = [self.record(), self.record(key='new', usera='new', year='2027', sortkey='0020'),
                   self.record(key='early', usera='early', sortkey='0001')]
        with contextlib.redirect_stderr(io.StringIO()):
            result = p.generate(records)
        self.assertEqual([x['id'] for x in result], ['new', 'early', 'stable-anchor'])

    def test_unknown_macros_and_duplicate_fields_fail(self):
        for text in ['@article{k, title=macro}', '@article{k, title={One}, title={Two}}',
                     '@article{k, title={Unclosed}']:
            with self.subTest(text=text), self.assertRaises(ValueError): p.read_bib(text)

    def test_standard_bibtex_macros_and_concatenation(self):
        entries = p.read_bib('@string{prefix = "One"} @article{k, title=prefix # { Two}}')
        self.assertEqual(entries[0]['title'], 'One Two')

    def test_invalid_dates_fail_in_both_generation_and_cv_sorting(self):
        for date in ['2026-99-99', '2026-02-30', '2026-00', '2026-01-00', '2026-1', '2025-12']:
            entry = self.record(keywords='journal', date=date)
            with self.subTest(date=date), self.assertRaises(ValueError):
                p.generate([entry])
            with self.subTest(date=date), self.assertRaises(ValueError):
                p.cv_groups([entry])

    def test_supported_date_precision_and_leap_year(self):
        self.assertEqual(p.date_parts('2026'), (2026, 0, 0))
        self.assertEqual(p.date_parts('2026-11'), (2026, 11, 0))
        self.assertEqual(p.date_parts('2024-02-29'), (2024, 2, 29))

    def test_title_link_prefers_doi_like_cv(self):
        record = p.generate([self.record(doi='10.123/test', url='https://example.org/other')])[0]
        self.assertEqual(record['titleUrl'], 'https://doi.org/10.123/test')

    def test_cv_classification_descending_labels_and_full_citation_keys(self):
        entries = [self.record(key='journal', keywords='journal'),
                   self.record(key='conference', keywords='conference', type='inproceedings'),
                   self.record(key='workshop', keywords='workshop', type='inproceedings')]
        text = p.cv_tex(p.cv_groups(entries))
        for prefix, key in [('J', 'journal'), ('C', 'conference'), ('W', 'workshop')]:
            self.assertIn(f'[{prefix}1]', text)
            self.assertIn(r'\fullcite{' + key + '}', text)

    def test_cv_date_order_is_separate_from_website_sortkey(self):
        entries = [self.record(key='june', keywords='conference', type='inproceedings',
                               eventdate='2026-06-20', sortkey='0001'),
                   self.record(key='november', keywords='conference', type='inproceedings',
                               date='2026-11', sortkey='0002')]
        group = p.cv_groups(entries)['conference']
        self.assertEqual([e['key'] for e in group], ['november', 'june'])
        text = p.cv_tex(p.cv_groups(entries))
        self.assertIn(r'[C2]}] \fullcite{november}', text)
        self.assertIn(r'[C1]}] \fullcite{june}', text)

    def test_cv_does_not_silently_guess_publication_category(self):
        for entry in [self.record(), self.record(keywords='conference')]:
            with self.assertRaises(ValueError): p.cv_groups([entry])

    def test_preprints_are_separate_from_journal_and_conference_counts(self):
        preprint = self.record(type='misc', key='preprint', keywords='preprint',
                              eprint='2608.12751', eprinttype='arxiv',
                              url='https://arxiv.org/abs/2608.12751')
        record = p.generate([preprint])[0]
        self.assertEqual(record['category'], 'preprint')
        self.assertEqual(record['venue'], 'arXiv:2608.12751')
        groups = p.cv_groups([self.record(keywords='journal'), preprint])
        self.assertEqual(len(groups['journal']), 1)
        self.assertEqual(len(groups['conference']), 0)
        self.assertIn(r'[P1]}] \fullcite{preprint}', p.cv_tex(groups))

    def test_invalid_or_missing_arxiv_identifier_fails(self):
        for changes in [{'eprint': ''}, {'eprint': 'not-an-id'}, {'eprinttype': 'unknown'}]:
            entry = self.record(type='misc', keywords='preprint',
                                eprint='2608.12751', eprinttype='arxiv')
            entry.update(changes)
            with self.assertRaises(ValueError): p.generate([entry])

if __name__ == '__main__': unittest.main()
