# coding: utf-8
"""Where World of Warships is installed, and which build folder is current."""

import os

# Tried in order when neither --game nor WOWS_DIR is given.
COMMON_GAME_DIRS = [
    drive + r':\SteamLibrary\steamapps\common\World of Warships' for drive in 'CDEFG'
] + [
    r'C:\Program Files (x86)\Steam\steamapps\common\World of Warships',
    r'C:\Games\World_of_Warships',
    r'C:\Games\World_of_Warships_ASIA',
    r'C:\Games\World_of_Warships_NA',
    r'C:\Games\World_of_Warships_EU',
]


def _is_game(path):
    return os.path.isfile(os.path.join(path, 'WorldOfWarships.exe'))


def game_dir(override=None):
    path = override or os.environ.get('WOWS_DIR')
    if path:
        if not _is_game(path):
            raise SystemExit('World of Warships not found at %s' % path)
        return path
    for path in COMMON_GAME_DIRS:
        if _is_game(path):
            return path
    raise SystemExit('World of Warships not found in the usual places '
                     '(pass --game or set WOWS_DIR)')


def build_dir(game, build=None):
    """bin/<build>; by default the newest one that has a res_mods folder."""
    bin_dir = os.path.join(game, 'bin')
    if build:
        path = os.path.join(bin_dir, build)
        if not os.path.isdir(os.path.join(path, 'res_mods')):
            raise SystemExit('%s has no res_mods folder' % path)
        return path
    builds = [n for n in os.listdir(bin_dir)
              if n.isdigit() and os.path.isdir(os.path.join(bin_dir, n, 'res_mods'))]
    if not builds:
        raise SystemExit('no build folder with res_mods under %s' % bin_dir)
    return os.path.join(bin_dir, max(builds, key=int))


def add_arguments(parser):
    parser.add_argument('--game', help='game folder (default: WOWS_DIR, '
                        'else the first usual install location that exists)')
    parser.add_argument('--build', help='build folder under bin/ (default: newest)')
