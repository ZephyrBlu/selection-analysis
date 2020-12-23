import json
from collections import namedtuple
from statistics import median
from pathlib import Path
from multiprocessing import Pool
from zephyrus_sc2_parser import parse_replay
from zephyrus_sc2_parser.game import GameObj
from sc2_tournament_analysis import recursive_parse

command_buildings = [
    'Nexus',
    'CommandCenter',
    'OrbitalCommand',
    'PlanetaryFortress',
    'Hatchery',
    'Lair',
    'Hive',
]

# ~7sec. PlayerStatsEvents occur at this interval throughout the game
TICK_SIZE = 160

PlayerTuple = namedtuple('PlayerTuple', ['name', 'race'])


def handle_replay(path, player_names, identifiers):
    parsed_ticks = {}

    replay = parse_replay(path, local=True, creep=False)

    for player in replay.players.values():
        tick_times = {
            'economy': [],
            'army': [],
            'infra': [],

            # new categories
            'creep': [],
            'queen': [],
        }
        # remove last selection since it technically has no end
        selections = player.selections[:-1]
        selections.sort(key=lambda x: x['start'])

        # list of selections in ~7sec intervals throughout the game
        ticks = [[]]

        # current tick
        tick = 1
        for s in selections:
            # as long as the selection ends before the end of the tick
            # we count it as part of the tick
            # tick * TICK_SIZE = upper gameloop limit for the current tick
            if s['end'] <= tick * TICK_SIZE:
                # add to current tick
                ticks[tick - 1].append(s)
            else:
                # create a new tick
                ticks.append([s])
                tick += 1

        for count, t in enumerate(ticks):
            all_times = []
            selection_times = {
                'economy': [],
                'army': [],
                'infra': [],

                # new categories
                'creep': [],
                'queen': [],
            }

            # iterating through all selections in the current tick
            for s in t:
                # if there are any objects of a group (economy/army/infra) in a selection
                # it counts for that groups. multiple groups can be counted in a single selection
                seen_group = set()
                diff = s['end'] - s['start']
                all_times.append(diff)

                # check the selection for each group
                # if we haven't already counted it for a group, record the selection length
                for obj in s['selection']:
                    # if obj.name == 'Egg' or obj.name == 'Larva':
                    #     continue
                    if 'Creep' in obj.name:
                        if 'creep' not in seen_group:
                            if player.name.lower() == 'serral':
                                print(path, s)
                            selection_times['creep'].append(diff)
                            seen_group.add('creep')
                    elif obj.name == 'Queen':
                        if 'queen' not in seen_group:
                            selection_times['queen'].append(diff)
                            seen_group.add('queen')
                    elif (
                        obj.name in command_buildings
                        or GameObj.WORKER in obj.type
                        or obj.name == 'Larva'
                    ):
                        if 'economy' not in seen_group:
                            selection_times['economy'].append(diff)
                            seen_group.add('economy')
                    elif (
                        GameObj.BUILDING in obj.type
                        or obj.name == 'Queen'
                        or 'Overlord' in obj.name
                        or 'Overseer' in obj.name
                    ):
                        if 'infra' not in seen_group:
                            selection_times['infra'].append(diff)
                            seen_group.add('infra')
                    elif GameObj.UNIT in obj.type:
                        if 'army' not in seen_group:
                            selection_times['army'].append(diff)
                            seen_group.add('army')

            # print(f'@{(count + 1) * 7}s, {round(sum(all_times) / 22.4, 2)}s')

            total_percentage = 0
            selection_percentages = {}

            # iterate through all selection times for all groups
            for n, v in selection_times.items():
                # if no selections for a particular group, skip it
                if not v:
                    continue

                # total selection time in seconds for the current group
                vt = sum(v) / 22.4

                # total selection time in seconds
                all_sec = sum(all_times) / 22.4

                # percentage of time the current group was selected
                percent = (vt / all_sec) * 100
                total_percentage += percent
                selection_percentages[n] = percent

            for n, v in selection_percentages.items():
                tick_times[n].append({
                    'tick': (count + 1) * TICK_SIZE,
                    'percent': round(v, 1),
                })

                # print(n.capitalize())
                # print(f'Selection Time: {vt}s ({round(percent, 2)}')

        parsed_ticks[PlayerTuple(player.name.lower(), player.race.lower())] = tick_times
    return parsed_ticks


# required for multiprocessing
if __name__ == '__main__':
    path = Path('replays')
    selections = {}

    for item in path.iterdir():
        print(f'In {item.name} directory')

        match_info_list = recursive_parse(
            sub_dir=item,
            # data_function is unused with multiprocessing
            data_function=handle_replay,
            multi=True,
        )

        results = []
        print(f'Parsing replays from {item.name}')

        # Pool multiprocessing for better throughput of parsing
        with Pool(10) as p:
            results = p.starmap(handle_replay, match_info_list)

        for r in results:
            for name, data in r.items():
                if name not in selections:
                    selections[name] = []
                selections[name].append(data)

        print(f'Replays from {item.name} parsed successfully')

    player_ticks = {}
    for player, player_data in selections.items():
        aggregated = {
            'economy': {},
            'army': {},
            'infra': {},

            # new categories
            'creep': {},
            'queen': {},
        }
        for game in player_data:
            for group, times in game.items():
                for t in times:
                    if t['tick'] not in aggregated[group]:
                        aggregated[group][t['tick']] = []
                    aggregated[group][t['tick']].append(t)

        aggregated_ticks = {}
        for group, ticks in aggregated.items():
            for tick, values in ticks.items():
                percentages = list(map(lambda x: x['percent'], values))
                avg = round(median(percentages), 1)

                if tick not in aggregated_ticks:
                    aggregated_ticks[tick] = {
                        'tick': tick,
                        group: avg,
                    }
                else:
                    aggregated_ticks[tick].update({group: avg})
        player_ticks[player.name] = sorted(list(aggregated_ticks.values()), key=lambda x: x['tick'])

    # with open('selection_timeline_loqc.json', 'w') as selection_data:
    #     json.dump(player_ticks, selection_data, indent=4)

    # with open('selection_timeline_loqc.js', 'w') as selection_data:
    #     selection_data.write(f'var selection_timeline_loqc = {player_ticks}')
