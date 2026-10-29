#!/usr/bin/env python3
# coding: utf-8
"""Run ModForge's own merge, lint and compile over our blueprints, offline.

Loads the ModForge installed in the game, read-only, under a small Python 2
compatibility shim, and feeds it the vanilla markup ModForge has already
cached for this build. Nothing in the game folder is written. What it
reports is what ModForge would refuse at the next client start.

Not covered: merging with other installed mods (deploy and read python.log
for that), <build>/<ubMountInBattle>, and <copy from=>.
"""

import argparse
import builtins
import glob
import os
import re
import sys
import tempfile
import types
import xml.etree.ElementTree as ET
import zlib

import wows_paths

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLUEPRINTS = os.path.join(ROOT, 'mod', 'res_mods', 'ForgeBlueprints')

MARKUP = 'gui/unbound/markup.xml'
STYLES = 'gui/unbound/styles.xml'
MOD_NAME = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')

FORGE_LOG = []


def _install_shims():
    """Make ModForge's pure modules importable under Python 3.

    Bytes stand in for py2 str and str for unicode, as in the client. Codec
    and Logger are replaced outright: Codec only resolves os, ElementTree and
    zlib, and Logger only forwards to the client's log."""
    builtins.unicode = str
    builtins.basestring = (str, bytes)
    builtins.unichr = chr
    builtins.xrange = range

    et = types.ModuleType('ElementTree_py2')
    et.__dict__.update(ET.__dict__)
    # py2 tostring() returns str, which ModForge treats as text.
    et.tostring = lambda el, *a, **k: ET.tostring(el, encoding='unicode')
    codec = types.ModuleType('Codec')
    codec._u1, codec._u2, codec._u3 = os, et, zlib
    sys.modules['Codec'] = codec

    logger = types.ModuleType('Logger')
    logger.logInfo = lambda *a: FORGE_LOG.append('info: ' + ', '.join(map(str, a)))
    logger.logError = lambda *a: FORGE_LOG.append('error: ' + ', '.join(map(str, a)))
    sys.modules['Logger'] = logger


def _patch_compile_path():
    """Spots on the compile path where py2 str-is-bytes semantics matter."""
    import UssLex, UssParse, UssSet, UssCompile

    def make_string_scanner(string, filename=None, line=0, column=0):
        if isinstance(string, bytes):
            string = string.decode('utf-8')
        return UssLex.Scanner(string, filename, line, column)
    UssLex.make_string_scanner = make_string_scanner
    UssParse.make_string_scanner = make_string_scanner

    # strhash() walks bytes; under py3 that yields ints, which ord() refuses.
    UssSet.ord = lambda c: c if isinstance(c, int) else ord(c)

    # The censor compares pool entries (bytes here) with str; decode them so
    # the comparison means what it does in the client.
    censored = UssCompile.censoredStrings
    UssCompile.censoredStrings = lambda pool: censored(
        [s.decode('utf-8') if isinstance(s, bytes) else s for s in pool])


class Sources(object):
    """The part of ModForge's Fragment.Sources the merge uses, over the
    vanilla files ModForge cached for this build."""

    def __init__(self, originals):
        import BlockSlice
        self._slice = BlockSlice
        self._dir = originals
        self._raw = {}
        self._index = {}

    def raw(self, rel):
        if rel not in self._raw:
            with open(os.path.join(self._dir, rel), encoding='utf-8') as f:
                self._raw[rel] = f.read()
        return self._raw[rel]

    def index(self, rel, tag, attr):
        key = (rel, tag, attr)
        if key not in self._index:
            self._index[key] = self._slice.top_level_index(self.raw(rel), tag, attr)
        return self._index[key]

    def find(self, rel, expr):
        raise RuntimeError('forge_check does not support <copy from=>')


class Forge(object):
    """The installed ModForge, loaded for checking."""

    def __init__(self, build):
        path = os.path.join(build, 'res_mods', 'PnFMods', 'ModForge')
        if not os.path.isfile(os.path.join(path, 'Ub1Lint.py')):
            raise SystemExit('ModForge not found at %s' % path)
        self.originals = os.path.join(path, '.installer_cache', 'originals')
        if not os.path.isfile(os.path.join(self.originals, MARKUP)):
            raise SystemExit('ModForge has not cached the vanilla markup yet; '
                             'start the client once with ModForge installed')
        with open(os.path.join(path, 'Main.py'), encoding='utf-8') as f:
            self.version = re.search(r"INSTALLER_VERSION = '([^']+)'", f.read()).group(1)

        sys.dont_write_bytecode = True  # leave no .pyc in the game folder
        sys.path.insert(0, path)
        _install_shims()
        import Build, Definitions, Manifest, Ub1Lint, UssCompile
        _patch_compile_path()
        self.Build, self.Definitions, self.Manifest = Build, Definitions, Manifest
        self.Ub1Lint, self.UssCompile = Ub1Lint, UssCompile
        self.sources = Sources(self.originals)
        self.classes, self.controllers = self._scene_classes()

    def _scene_classes(self):
        path = os.path.join(self.originals, 'gui', 'flash',
                            'consumer_main_scene.swf.classes')
        if not os.path.isfile(path):
            return None, None
        classes, controllers = set(), set()
        with open(path, encoding='utf-8') as f:
            for line in f.read().split('\n')[1:]:
                kind, _sep, name = line.partition('\t')
                if kind == 'C':
                    classes.add(name)
                elif kind == 'U':
                    controllers.add(name)
        return frozenset(classes), frozenset(controllers)

    def check(self, blueprint, dump=None):
        """(list of findings, refused?) for one blueprint. With dump, the
        merged definitions are also written there, as ModForge would emit
        them."""
        del FORGE_LOG[:]
        with open(blueprint, 'rb') as f:
            data = f.read()
        try:
            manifest = self.Manifest.parseManifest(blueprint, data)
        except self.Manifest.ManifestError as exc:
            return ['refused: invalid manifest: %s' % exc], True
        out = []
        if not MOD_NAME.match(manifest.modName):
            out.append('refused: mod name %r is not an identifier' % manifest.modName)
        need = manifest.installerRequirement
        if need and not self.Manifest.satisfiesConstraint(self.version, need):
            out.append('refused: needs ModForge %s, installed is %s' % (need, self.version))
        if manifest.builds:
            out.append('note: <build>/<ubMountInBattle> are not checked here')

        emitted = self._merge(manifest, out)
        if dump:
            os.makedirs(dump, exist_ok=True)
            for (_namespace, name), data in emitted:
                with open(os.path.join(dump, name + '.xml'), 'wb') as f:
                    f.write(data)
        self._lint(emitted, out)
        self._compile(emitted, out)
        out.extend('modforge ' + line for line in FORGE_LOG)
        refused = any(line.startswith('refused') for line in out)
        return out, refused

    def _merge(self, manifest, out):
        Definitions = self.Definitions
        merger = Definitions.Merger(self.sources)
        emitted = []
        for key, contributions in Definitions.collect([manifest]):
            label = Definitions.label(*key)
            failed = set()
            try:
                data, is_new = merger.build(key, contributions, set(), failed)
            except Exception as exc:
                out.append('refused: %s: %s: %s' % (label, type(exc).__name__, exc))
                continue
            if failed:
                out.append('refused: %s does not apply (reason below)' % label)
            elif data is None:
                out.append('note: %s changes nothing' % label)
            else:
                out.append('%s %s (%d bytes)'
                           % ('created  ' if is_new else 'overrides', label, len(data)))
                emitted.append((key, data))
        return emitted

    def _lint(self, emitted, out):
        Ub1Lint = self.Ub1Lint
        blocks = set(self.sources.index(MARKUP, 'block', 'className'))
        css = set(self.sources.index(STYLES, 'css', 'name'))
        for (namespace, name), _data in emitted:
            (blocks if namespace == 'block' else css).add(name)
        ctx = Ub1Lint.Context(classNames=blocks, cssNames=css,
                              classes=self.classes, controllers=self.controllers)
        quiet = self.Definitions.Merger(self.sources, quiet=True)
        for key, data in emitted:
            label = self.Definitions.label(*key)
            try:
                doc, _is_new = quiet.baseline(*key)
                base = Ub1Lint.lintDocument(ET.fromstring(self.Build.serialize(doc)), ctx)
                found = Ub1Lint.introduced(Ub1Lint.lintDocument(ET.fromstring(data), ctx), base)
            except Exception as exc:
                out.append('refused?: lint crashed on %s: %s: %s'
                           % (label, type(exc).__name__, exc))
                continue
            for f in found:
                out.append('%s: %s %s %s at %s: %s'
                           % ('refused' if Ub1Lint.refuses(f) else 'warning',
                              label, f.severity, f.code, f.where, f.message))

    def _compile(self, emitted, out):
        """One SWF over all of it, censor check included, as the installer does."""
        if not emitted:
            return
        tmp = tempfile.mkdtemp(prefix='forge_check_')
        paths = []
        try:
            for (namespace, name), data in emitted:
                path = os.path.join(tmp, '%s_%s.xml' % (namespace, name))
                with open(path, 'wb') as f:
                    f.write(data)
                paths.append(path)
            swf, count = self.UssCompile.compileMarkup(paths, None, allowEmpty=True)
            out.append('compiled %d expression(s) into a %d-byte SWF'
                       % (count, len(swf) if swf else 0))
        except Exception as exc:
            out.append('refused: does not compile: %s' % exc)
        finally:
            for path in paths:
                os.remove(path)
            os.rmdir(tmp)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    wows_paths.add_arguments(parser)
    parser.add_argument('blueprints', nargs='*',
                        help='blueprint files (default: mod/res_mods/ForgeBlueprints/*.xml)')
    parser.add_argument('--dump', metavar='DIR',
                        help='also write the merged definitions into DIR')
    args = parser.parse_args()

    forge = Forge(wows_paths.build_dir(wows_paths.game_dir(args.game), args.build))
    print('ModForge %s, vanilla markup from %s\n' % (forge.version, forge.originals))
    files = args.blueprints or sorted(glob.glob(os.path.join(BLUEPRINTS, '*.xml')))
    if not files:
        raise SystemExit('no blueprints to check')
    refused = 0
    for path in files:
        print(path)
        findings, bad = forge.check(path, args.dump)
        for line in findings:
            print('  ' + line)
        print('  => %s\n' % ('ModForge would NOT install this mod' if bad
                             else 'passes ModForge lint and compile'))
        refused += bad
    sys.exit(1 if refused else 0)


if __name__ == '__main__':
    main()
