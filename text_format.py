from StringIO import StringIO

import re
import numpy
from seating import State


def read_text(filename):

    group_names = []
    group_weights = []
    groups = []

    group = []
    position = []

    with open(filename, "rb") as f:
        for line in f:
            if line.startswith('#'):
                name, weight_str = re.match(r"#\s*(\S*)\s*(?:\((\d+)\))?", line.strip()).groups()
                group_names.append(name)
                weight = int(weight_str) if weight_str else 1
                group_weights.append(weight)

                if position:
                    group.append(position)
                    position = []
                if group:
                    groups.append(group)
                    group = []
            elif line.strip() == '':
                if position:
                    group.append(position)
                    position = []
            else:
                fixed = line.startswith('*')
                if fixed:
                    line = line[1:]
                position.append([line.strip(), fixed])

        if position:
            group.append(position)
        if group:
            groups.append(group)

    cnt = 0
    group_indexes = []
    for group in groups:
        group_indexes.append((cnt, cnt + len(group)))
        cnt += len(group)

    names = list({name
                  for group in groups
                  for position in group
                  for (name, _) in position})
    names.sort()

    group_indexes = group_indexes

    seating = numpy.zeros((len(names), group_indexes[-1][1]), dtype=int)
    fixed = numpy.zeros((len(names), group_indexes[-1][1]), dtype=bool)

    persons_by_name = {name: idx for idx, name in enumerate(names)}
    cnt = 0
    for group in groups:
        for position in group:
            for name, is_fixed in position:
                row = persons_by_name[name]
                seating[row, cnt] = 1
                fixed[row, cnt] = is_fixed
            cnt += 1

    geometry = seating.copy().transpose()

    return State(names=names,
                 group_names=group_names,
                 group_indexes=group_indexes,
                 group_weights=group_weights,
                 seating=seating,
                 fixed=fixed,
                 geometry=geometry)


def write_text(state):
    result = StringIO()

    for group_name, (i, j), weight in zip(state.group_names, state.group_indexes, state.group_weights):
        weight_str = (" (%d)" % weight) if weight > 1 else ''
        result.write('# ' + group_name + weight_str + "\n\n")
        for t in range(i, j):
            for p in numpy.where(state.seating[:, t] == 1)[0]:
                if state.fixed[p, t]:
                    result.write('*')
                result.write(state.names[p] + '\n')
            result.write('\n')
        result.write('\n')

    return result.getvalue()
