import json
from pathlib import Path
from multiprocessing import Pool
from zephyrus_sc2_parser import parse_replay
from zephyrus_sc2_parser.game import GameObj
from sc2_tournament_analysis import recursive_parse

command_buildings = [
    'Nexus',
    'CommandCenter',
    'OrbitalCommand',
    'PlanteryFortress',
    'Hatchery',
    'Lair',
    'Hive',
]

# ~7sec. PlayerStatsEvents occur at this interval throughout the game
TICK_SIZE = 160


def handle_replay(path):
    replay = parse_replay(path, local=True, creep=False)

    tick_times = {
        'economy': [],
        'army': [],
        'infra': [],
    }
    # remove last selection since it technically has no end
    selections = replay.players[1].selections[:-1]
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
                if (
                    obj.name in command_buildings
                    or GameObj.WORKER in obj.type
                ):
                    if 'economy' not in seen_group:
                        selection_times['economy'].append(diff)
                        seen_group.add('economy')
                elif GameObj.UNIT in obj.type:
                    if 'army' not in seen_group:
                        selection_times['army'].append(diff)
                        seen_group.add('army')
                elif GameObj.BUILDING in obj.type:
                    if 'infra' not in seen_group:
                        selection_times['infra'].append(diff)
                        seen_group.add('infra')

        print(f'@{(count + 1) * 7}s, {round(sum(all_times) / 22.4, 2)}s')

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

            tick_times[n].append({
                'tick': (count + 1) * TICK_SIZE,
                'seconds': round(vt, 3),
                'percent': round(percent, 1),
            })

            print(n.capitalize())
            print(f'Selection Time: {vt}s ({round(percent, 2)}')

    return tick_times


# required for multiprocessing
if __name__ == '__main__':
    path = Path('replays')
    selections = []

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

        selections.extend(results)
        print(f'Replays from {item.name} parsed successfully')

    print(selections)

    # with open('selections.json', 'w') as selection_data:
    #     json.dump(tick_times, selection_data, indent=4)
