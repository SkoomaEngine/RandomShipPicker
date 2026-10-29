#!/usr/bin/env python3
# coding: utf-8
"""Copy mod/res_mods into the game's current build folder, or take it back out.

Only files that exist under mod/res_mods are ever written or deleted, so the
game's other mods are never touched. ModForge picks the change up the next
time the client starts.
"""

import argparse
import filecmp
import os
import shutil
import sys

import wows_paths

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, 'mod', 'res_mods')

# Files earlier versions of this project put into the game. They are deleted
# on every deploy and on --remove.
RETIRED = [
    os.path.join('ForgeBlueprints', 'RSP_Probe.xml'),
]


def mod_files():
    for base, _dirs, files in os.walk(SOURCE):
        for name in sorted(files):
            yield os.path.relpath(os.path.join(base, name), SOURCE)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    wows_paths.add_arguments(parser)
    parser.add_argument('--remove', action='store_true',
                        help='delete the files this mod put into the game')
    parser.add_argument('--dry-run', action='store_true',
                        help='print what would happen and change nothing')
    args = parser.parse_args()

    target = os.path.join(
        wows_paths.build_dir(wows_paths.game_dir(args.game), args.build),
        'res_mods')
    files = list(mod_files())
    if not files:
        sys.exit('nothing to deploy under %s' % SOURCE)
    print('target: %s' % target)

    for rel in files:
        src = os.path.join(SOURCE, rel)
        dst = os.path.join(target, rel)
        if args.remove:
            if not os.path.isfile(dst):
                print('  absent  %s' % rel)
                continue
            print('  remove  %s' % rel)
            if not args.dry_run:
                os.remove(dst)
            continue
        if os.path.isfile(dst) and filecmp.cmp(src, dst, shallow=False):
            print('  same    %s' % rel)
            continue
        print('  %s %s' % ('update ' if os.path.exists(dst) else 'add    ', rel))
        if not args.dry_run:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)

    for rel in RETIRED:
        dst = os.path.join(target, rel)
        if os.path.isfile(dst):
            print('  retire  %s' % rel)
            if not args.dry_run:
                os.remove(dst)

    if args.dry_run:
        print('dry run: nothing was changed')
    else:
        print('done; ModForge applies it on the next client start')


if __name__ == '__main__':
    main()
