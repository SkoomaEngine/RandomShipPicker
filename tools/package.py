#!/usr/bin/env python3
# coding: utf-8
"""Build the release zip: dist/RandomShipPicker-<version>.zip.

The zip holds res_mods/ (as deployed into bin/<build>/) plus every file in
release/. The version comes from the blueprint's <mod version=...>, and the
build stops if CHANGELOG.md has no entry for it or if forge_check refuses
the blueprint.
"""

import argparse
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES_MODS = os.path.join(ROOT, 'mod', 'res_mods')
RELEASE = os.path.join(ROOT, 'release')
DIST = os.path.join(ROOT, 'dist')
BLUEPRINT = os.path.join(RES_MODS, 'ForgeBlueprints', 'RSP_RandomShipPicker.xml')


def blueprint_version():
    return ET.parse(BLUEPRINT).getroot().get('version')


def changelog_has(version):
    with open(os.path.join(RELEASE, 'CHANGELOG.md'), encoding='utf-8') as f:
        return re.search(r'^## %s\b' % re.escape(version), f.read(), re.M) is not None


def files_under(base, prefix):
    for top, _dirs, names in os.walk(base):
        for name in sorted(names):
            path = os.path.join(top, name)
            yield path, os.path.join(prefix, os.path.relpath(path, base)).replace(os.sep, '/')


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--skip-check', action='store_true',
                        help='do not run forge_check (needs the game installed)')
    args = parser.parse_args()

    version = blueprint_version()
    if not version:
        sys.exit('no version attribute in %s' % BLUEPRINT)
    if not changelog_has(version):
        sys.exit('release/CHANGELOG.md has no "## %s" entry' % version)
    if not args.skip_check:
        check = subprocess.run([sys.executable, '-B', os.path.join(ROOT, 'tools', 'forge_check.py'), BLUEPRINT])
        if check.returncode:
            sys.exit('forge_check refused the blueprint; nothing packaged')

    os.makedirs(DIST, exist_ok=True)
    mod_files = list(files_under(RES_MODS, 'res_mods'))
    # The full release, and a res_mods-only copy for installers that extract
    # an archive straight into bin/<build>/, such as Aslain's custom mods.
    for name, entries in (('RandomShipPicker-%s.zip', mod_files + list(files_under(RELEASE, ''))),
                          ('RandomShipPicker-%s-res_mods-only.zip', mod_files)):
        out = os.path.join(DIST, name % version)
        with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zf:
            for path, arc in entries:
                zf.write(path, arc)
                print('  %s' % arc)
        print('wrote %s' % out)


if __name__ == '__main__':
    main()
