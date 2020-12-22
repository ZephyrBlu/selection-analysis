This is a small project to analyze the selections of pro players from ASUS ROG 2020 replays. You can easily re-use this script for other replays, or modify it to analyze different players, races, etc.

The only external dependency is `sc2_tournament_analysis` which is a tiny helper library I wrote for parsing tournament packs, since replays tend to be deeply nested. You can install this using pip like so: `pip install sc2_tournament_analysis`. Or download the [source code](https://github.com/ZephyrBlu/sc2-tournament-analysis) (I think it's up to date) and use it directly.

# Usage

`analyze.py` contains the script for analyzing replays in the `replays/` directory. If you want to analyze different replays simply add/remove them from the `replays/` directory.

Currently the script is hardcoded to parse all replays, but only analyze games played by [Byun, Maru, Reynor and ShoWTimE](https://github.com/ZephyrBlu/selection-analysis/blob/master/analyze.py#L128). If you wish to analyze by race instead then you will want to alter [this line](https://github.com/ZephyrBlu/selection-analysis/blob/master/analyze.py#L162) to `if player.race not in <insert list races you want to analyze>` and alter [this line](https://github.com/ZephyrBlu/selection-analysis/blob/master/analyze.py#L190) to record data by `player.race` instead of `player.name`.

By default the script uses Python's multiprocessing module and the parser does not make network calls to speed up parsing. The ASUS ROG replays (~100) take ~120sec to parse and process.

Note: Multiprocessing will use a significant amount of your CPU, so be aware of this if you aren't running a beefy setup.

# Why is the parser included?

Because this script only works with a new version of the parser that supports selection tracking, and that version is currently still being developed. In the near future the parser included in the repo will be obsolete or unneeded.
