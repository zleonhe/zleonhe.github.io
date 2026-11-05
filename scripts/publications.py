#!/usr/bin/env python3
"""Generate website data and CV citations from the shared BibLaTeX database."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

from pybtex.database import parse_string
from pybtex.exceptions import PybtexError

ROOT = Path(__file__).resolve().parents[1]
BIB = ROOT / 'cv/publication.bib'
OUTPUT = ROOT / 'src/data/publications.json'
RESOURCES = [('paper', 'Paper'), ('slides', 'Slides'), ('code', 'Code'),
             ('poster', 'Poster'), ('preprint', 'arXiv')]


def read_bib(text):
    try:
        database = parse_string(text, 'bibtex')
    except PybtexError as error:
        raise ValueError(str(error)) from error
    entries = []
    for key, entry in database.entries.items():
        if entry.type not in ('article', 'inproceedings', 'misc'):
            raise ValueError(f'Unsupported entry type {entry.type} in {key}')
        entries.append({'type': entry.type, 'key': key, **entry.fields,
                        'author': entry.persons.get('author', [])})
    return entries


def plain(value):
    value = value.replace('~', ' ')
    for a, b in [(r'\&', '&'), (r'\%', '%'), (r'\_', '_'), (r'\#', '#')]:
        value = value.replace(a, b)
    if '\\' in value: raise ValueError(f'Unsupported LaTeX command in display text: {value}')
    return re.sub(r'\s+', ' ', value.replace('{', '').replace('}', '')).strip()


def author_names(value):
    names = []
    for person in value:
        parts = person.first_names + person.middle_names + person.prelast_names + person.last_names
        name = plain(' '.join(parts))
        if person.lineage_names:
            name += ', ' + plain(' '.join(person.lineage_names))
        names.append(name)
    return names


def date_parts(value):
    """Validate the supported ISO date precisions without inventing a sort date."""
    if not re.fullmatch(r'\d{4}(?:-\d{2}(?:-\d{2})?)?', value):
        raise ValueError(f'Invalid date: {value}')
    parts = [int(part) for part in value.split('-')]
    year, month, day = (parts + [0, 0])[:3]
    dt.date(year, month or 1, day or 1)
    # Explicit zero is invalid; only missing components get the validation default.
    if len(parts) > 1 and month == 0 or len(parts) > 2 and day == 0:
        raise ValueError(f'Invalid date: {value}')
    return year, month, day


def dates(value):
    ends = [dt.date.fromisoformat(v) for v in value.split('/')]
    if len(ends) not in (1, 2) or (len(ends) == 2 and ends[1] < ends[0]):
        raise ValueError(f'Invalid eventdate: {value}')
    def month(d): return ['Jan.', 'Feb.', 'Mar.', 'Apr.', 'May', 'Jun.', 'Jul.', 'Aug.', 'Sept.', 'Oct.', 'Nov.', 'Dec.'][d.month-1]
    a, b = ends[0], ends[-1]
    if a == b: return f'{month(a)} {a.day}, {a.year}'
    if a.year != b.year: return f'{month(a)} {a.day}, {a.year}–{month(b)} {b.day}, {b.year}'
    if a.month != b.month: return f'{month(a)} {a.day}–{month(b)} {b.day}, {b.year}'
    return f'{month(a)} {a.day}–{b.day}, {b.year}'


def valid_url(value):
    if value.startswith('/') and not value.startswith('//'): return True
    u = urlsplit(value)
    return u.scheme == 'https' and bool(u.netloc)


def cv_groups(entries):
    """Classify explicitly; sort the CV without changing website order/anchors."""
    groups = {name: [] for name in ('journal', 'conference', 'workshop', 'preprint')}
    for entry in entries:
        category = entry.get('keywords', '')
        if category not in groups:
            raise ValueError(f"Specify journal/conference/workshop/preprint keywords for {entry['key']}")
        if ((entry['type'] == 'article') != (category == 'journal') or
                (entry['type'] == 'misc') != (category == 'preprint')):
            raise ValueError(f"Entry type/category conflict in {entry['key']}")
        groups[category].append(entry)
    def order(entry):
        date = entry.get('date', '')
        if not date and entry['type'] == 'inproceedings':
            date = entry.get('eventdate', '').split('/')[0]
        # Missing month/day are not invented. Dated entries precede undated ones;
        # the editorial sortkey breaks ties and orders undated entries.
        year, month, day = date_parts(date) if date else (int(entry['year']), 0, 0)
        if year != int(entry['year']):
            raise ValueError(f"CV date/year conflict in {entry['key']}")
        monthday = month * 100 + day
        return (-int(entry['year']), -monthday, int(entry['sortkey']))
    for group in groups.values():
        group.sort(key=order)
    return groups


def cv_tex(groups):
    lines = ['% Generated from publication.bib; do not edit.']
    for category, prefix, title in [('journal', 'J', 'Journal Articles'),
            ('conference', 'C', 'Conference Papers'), ('workshop', 'W', 'Workshop Papers'),
            ('preprint', 'P', 'Preprints')]:
        group = groups[category]
        if not group:
            continue
        lines += [f'\\subsection{{{title}}}', r'\begin{cvpublications}']
        for i, entry in enumerate(group):
            label = f'{prefix}{len(group)-i}'
            lines.append(r'\item[\textnormal{[' + label + r']}] \fullcite{' + entry['key'] + '}.')
        lines.append(r'\end{cvpublications}')
    return '\n'.join(lines) + '\n'


def generate(entries):
    seen = {name: set() for name in ['key', 'usera', 'sortkey', 'doi']}
    titles, records = {}, []
    for e in entries:
        preprint = e['type'] == 'misc'
        venue = 'journal' if e['type'] == 'article' else 'booktitle'
        required = ['eprint', 'eprinttype'] if preprint else [venue]
        for field in ['key', 'title', 'author', 'year', 'usera', 'sortkey', *required]:
            if not e.get(field): raise ValueError(f"Missing {field} in {e['key']}")
        if preprint and (e['eprinttype'] != 'arxiv' or not re.fullmatch(r'\d{4}\.\d{4,5}', e['eprint'])):
            raise ValueError(f"Expected an arxiv eprint identifier in {e['key']}")
        for field, values in seen.items():
            value = e.get(field, '').casefold()
            if value and value in values: raise ValueError(f"Duplicate {field}: {e[field]}")
            if value: values.add(value)
        year = int(e['year'])
        if e.get('date') and date_parts(e['date'])[0] != year:
            raise ValueError(f"date/year mismatch in {e['key']}")
        if e.get('eventdate') and dt.date.fromisoformat(e['eventdate'].split('/')[0]).year != year:
            raise ValueError(f"eventdate/year mismatch in {e['key']}")
        title = plain(e['title'])
        normalized = re.sub(r'\W', '', title.casefold())
        if normalized in titles:
            print(f"Note: shared title (check distinct publication versions): {titles[normalized]}, {e['key']}", file=sys.stderr)
        titles[normalized] = e['key']
        links = [{'label': label, 'url': e[field]} for field, label in RESOURCES if e.get(field)]
        title_url = f"https://doi.org/{e['doi']}" if e.get('doi') else e.get('url')
        for url in [*(x['url'] for x in links), *([title_url] if title_url else [])]:
            if not valid_url(url): raise ValueError(f"Invalid URL in {e['key']}: {url}")
            if url.startswith('/') and not (ROOT/'public'/url.lstrip('/')).is_file():
                raise ValueError(f'Missing local resource: {url}')
        location = plain(e.get('location', ''))
        when = dates(e['eventdate']) if e.get('eventdate') else str(year)
        records.append({'id': e['usera'], 'key': e['key'], 'year': year,
            'category': e.get('keywords', ''),
            'authors': author_names(e['author']), 'title': title, 'titleUrl': title_url,
            'venue': f"arXiv:{e['eprint']}" if preprint else plain(e[venue]),
            'location': (location + ', ' if location else '') + when + '.',
            'note': plain(e.get('note', '')).strip('()'), 'links': links,
            '_sort': int(e['sortkey'])})
    records.sort(key=lambda p: (-p['year'], p['_sort']))
    for p in records: del p['_sort']
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Validate and check generated JSON without writing')
    parser.add_argument('--cv', action='store_true', help='Also generate the grouped CV citation list in cv/build/')
    args = parser.parse_args()
    try:
        entries = read_bib(BIB.read_text())
        records = generate(entries)
        groups = cv_groups(entries)
        by_key = {record['key']: record for record in records}
        for category, prefix in [('journal', 'J'), ('conference', 'C'),
                                 ('workshop', 'W'), ('preprint', 'P')]:
            group = groups[category]
            for index, entry in enumerate(group):
                by_key[entry['key']]['label'] = f'{prefix}{len(group) - index}'
                by_key[entry['key']]['cvOrder'] = index
        content = json.dumps(records, ensure_ascii=False, indent=2) + '\n'
        if args.check:
            if not OUTPUT.exists() or OUTPUT.read_text() != content:
                raise ValueError('Generated data is stale; run python3 scripts/publications.py')
        else:
            OUTPUT.write_text(content)
            if args.cv:
                target = ROOT / 'cv/build/publications.tex'
                target.parent.mkdir(exist_ok=True)
                target.write_text(cv_tex(groups))
                print('CV groups: ' + ', '.join(f'{name}={len(group)}' for name, group in groups.items()))
        print(f"{'Checked' if args.check else 'Generated'} {len(records)} publications from cv/publication.bib")
    except (ValueError, KeyError) as error:
        parser.exit(1, f'Publication data error: {error}\n')

if __name__ == '__main__': main()
