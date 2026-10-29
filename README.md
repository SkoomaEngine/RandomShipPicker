# Random Ship Picker

[中文说明](README_zh.md)

A World of Warships client mod. It adds a **Random** button to the port's carousel filter row. One click selects a ship drawn uniformly at random from the ships that match your current carousel filters, and the carousel scrolls to it.

It is a pure UI mod: a single ModForge blueprint (`RSP_RandomShipPicker.xml`), with no executables and no Python. It does not touch the Unbound 2 carousel, so it coexists with Aslain's modpack and Port Interface.

Current version: 1.0.0, tested on client 15.9.0 (Asia server).

## For players

Download the zip from [Releases](../../releases). Installation, usage and the things to know are in [release/README.md](release/README.md).

In short:

- It requires ModForge, which Aslain's modpack installs.
- After each pick the mod briefly flips "Hide ships that don't match the filter" and puts it back about 0.15 s later. That is what makes the carousel scroll.
- Only the game's own filters count. Filters that other mods add inside the carousel are not visible to it.

## Repository layout

| Path | Contents |
|---|---|
| `mod/res_mods/ForgeBlueprints/RSP_RandomShipPicker.xml` | The mod itself |
| `release/` | README (English and Chinese) and CHANGELOG shipped in the release zip |
| `tools/forge_check.py` | Runs the game's installed ModForge offline over the blueprints: merge, lint and compile, with the same verdict ModForge gives at client start |
| `tools/deploy.py` | Copies `mod/res_mods/` into the game. `--remove` takes it back out, `--dry-run` only previews |
| `tools/checklog.py` | Summarises `profile/python.log`: this mod's ModForge lines, the run summary and AS3 errors |
| `tools/package.py` | Builds `dist/RandomShipPicker-<version>.zip` after running `forge_check` and checking that the CHANGELOG has the version |
| `docs/v1-test.md` | In-game test steps for 1.0.0 (Chinese) |
| `probe/` | The diagnostic probe used during development to measure how the carousel behaves, and its test notes (Chinese). Retired; never deployed by the tools |

## Development

You need Python 3 and a World of Warships install with ModForge. Run these from the repository root:

```text
python tools/forge_check.py          # would ModForge refuse the blueprint?
python tools/deploy.py --dry-run     # preview what would be copied
python tools/deploy.py               # deploy; takes effect at the next client start
python tools/deploy.py --remove      # undeploy; ModForge restores vanilla at the next start
python tools/checklog.py             # summary of the latest client start
python tools/package.py              # build the release zip into dist/
```

The tools look for the game in the usual Steam and Wargaming Game Center locations. Use `--game` or the `WOWS_DIR` environment variable to point them elsewhere, and `--build` to pick a `bin\<build>` folder other than the newest.

`deploy.py` only writes or deletes files that exist under `mod/res_mods/`, plus the retired probe blueprint `RSP_Probe.xml`. `forge_check.py` only reads from the game folder.

## License

[MIT](LICENSE)
