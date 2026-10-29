# Random Ship Picker

A World of Warships client mod. It adds a **Random** button to the port's carousel filter row. One click selects a ship drawn uniformly at random from the ships that match your current carousel filters, and the carousel scrolls to it.

The mod is a single plain-text ModForge blueprint (XML). It contains no executables and no Python code, and it reads no files. Open it in any text editor to see exactly what it does.

## Requirements

- World of Warships PC client. Tested on 15.9.0.
- ModForge 1.0.0 or later.

## Installation

1. Find your game's newest build folder: `World of Warships\bin\<largest number>\`.
2. Copy the `res_mods` folder from this package into it. The file should end up at `bin\<build>\res_mods\ForgeBlueprints\RSP_RandomShipPicker.xml`.
3. Start the game. The **Random** button appears at the right end of the carousel filter row. Its label is translated by the game's own localization.

After a game update creates a new `bin\<build>` folder, copy the file again unless your mod manager migrates `res_mods` for you.

## Uninstallation

Delete `res_mods\ForgeBlueprints\RSP_RandomShipPicker.xml` and restart the game. ModForge restores the original interface.

## Usage

- Set the carousel filters you want, then click **Random**.
- It works whether "Hide ships that don't match the filter" is on or off.
- Every click is an independent draw, so the same ship can come up twice in a row.
- If no ship matches the filters, the button is dimmed and does nothing.

## Things to know

- **The mod briefly flips one setting.** Selecting a ship does not make the carousel scroll, but changing "Hide ships that don't match the filter" does. After each pick, the mod flips that setting and puts your value back about 0.15 s later.
  - Normally you won't notice anything, and your setting stays as it was.
  - If you leave the port or close the game within that fraction of a second, the setting may stay flipped. Switch it back in the carousel filter settings.
  - Clicks are ignored until the setting has been restored.
- **Only the game's own filters count**: tier, type, nation, special, rarity and the ship-name search. Filters that other mods add inside the carousel are not visible to this mod. Examples are Port Interface's captain, win-rate and battle-count filters.
- Only ships you own can be picked.

## Compatibility

- The button is inserted into the vanilla port carousel panel (`ShipsCarouselPanel`). All other logic lives in the mod's own definitions, prefixed `RSP_`.
- The Unbound 2 ship carousel is not modified, so carousel mods such as Aslain's Port Interface keep working.
- If you use another random-ship button, for example the "Random Ship Selector" component of Port Interface, consider disabling one of them.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).
