#!/usr/bin/env python3
# coding: utf-8
"""Summarise what one client start logged about this mod.

Prints, for the newest session in profile/python.log (or an older one with
--session): the ModForge lines that name this mod or the definitions it
edits, every ModForge error, the ModForge run summary, and the AS3 errors
the client caught, grouped with their stack traces.
"""

import argparse
import os
import re
from collections import OrderedDict

import wows_paths

OURS = re.compile(r'RSP_\w*|\bShipsCarouselPanel\b|\bCarouselFilters\b')
SUMMARY = re.compile(r'\[ModForge\] (done in |definitions: )')
SESSION_START = re.compile(r'^WorldOfWarships\S* .* starting on ')
STAMP = re.compile(r'^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+: ')


def sessions(lines):
    starts = [i for i, line in enumerate(lines) if SESSION_START.match(line)]
    if not starts:
        return [(0, len(lines))]
    return list(zip(starts, starts[1:] + [len(lines)]))


def as3_errors(lines):
    """{message + stack: (count, first line)}, in order of first appearance."""
    groups = OrderedDict()
    i = 0
    while i < len(lines):
        line = lines[i]
        if '[Scaleform] Error' not in line:
            i += 1
            continue
        block = [STAMP.sub('', line).strip()]
        j = i + 1
        while j < len(lines) and (lines[j].startswith('\tat ')
                                  or lines[j].startswith('AS3 stack')):
            block.append(lines[j].strip())
            j += 1
        key = '\n    '.join(block)
        count, first = groups.get(key, (0, line[:23]))
        groups[key] = (count + 1, first)
        i = j
    return groups


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    wows_paths.add_arguments(parser)
    parser.add_argument('--log', help='path to python.log (default: <game>/profile/python.log)')
    parser.add_argument('--session', type=int, default=1,
                        help='1 = newest client start, 2 = the one before, ...')
    args = parser.parse_args()

    path = args.log or os.path.join(wows_paths.game_dir(args.game), 'profile', 'python.log')
    with open(path, encoding='utf-8', errors='replace') as f:
        lines = f.read().split('\n')
    spans = sessions(lines)
    if not 1 <= args.session <= len(spans):
        raise SystemExit('the log holds %d session(s)' % len(spans))
    start, end = spans[-args.session]
    part = lines[start:end]
    print('%s\n%s\n' % (path, part[0].strip() if part else ''))

    forge = [l for l in part if '[ModForge]' in l]
    print('== ModForge: lines about this mod')
    for line in forge:
        if OURS.search(line):
            print('  ' + STAMP.sub('', line).strip())
    print('== ModForge: errors')
    for line in forge:
        if ': ERROR: ' in line:
            print('  ' + STAMP.sub('', line).strip()[:400])
    print('== ModForge: summary')
    for line in forge:
        if SUMMARY.search(line):
            print('  ' + STAMP.sub('', line).strip())
    if not forge:
        print('  (no ModForge lines: did the client start with mods enabled?)')

    groups = as3_errors(part)
    print('== AS3 errors: %d distinct, %d total'
          % (len(groups), sum(c for c, _ in groups.values())))
    for key, (count, first) in groups.items():
        print('  x%d, first at %s\n    %s' % (count, first, key))


if __name__ == '__main__':
    main()
