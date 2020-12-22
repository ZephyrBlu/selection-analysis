This is a small project to analyze the selections of pro players from ASUS ROG 2020 replays. You can easily re-use this script for other replays, or modify it to analyze different players, races, etc.

The only external dependency is `sc2_tournament_analysis` which is a tiny helper library I wrote for parsing tournament packs, since replays tend to be deeply nested. You can install this using pip like so: `pip install sc2_tournament_analysis`. Or download the [source code](https://github.com/ZephyrBlu/sc2-tournament-analysis) (I think it's up to date) and use it directly.

# Usage

Simply run `analyze.py` and the processed data will be output to `selection_timeline.json`.

If you want to analyze different replays simply add/remove them from the `replays/` directory.

Currently the script is hardcoded to parse and analyze all replays. If you want to display only particular players you can modify that in the HTML file. If you want to analyze by race, you will need to make some modifications.

By default the script uses Python's multiprocessing module and the parser does not make network calls to speed up parsing. The ASUS ROG replays (~100) take ~120sec to parse and process.

Note: Multiprocessing will use a significant amount of your CPU, so be aware of this if you aren't running a beefy setup.

# Why is the parser included?

Because this script only works with a new version of the parser that supports selection tracking, and that version is currently still being developed. In the near future the parser included in the repo will be obsolete or unneeded.
