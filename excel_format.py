import sys
from io import BytesIO

import re
import numpy
from seating import State, optimize, dump, report, start_seating
from text_format import read_text, write_text
from xlrd import open_workbook
from xlutils.margins import number_of_good_rows, number_of_good_cols
from bunch import Bunch
from xlwt import Workbook, easyxf


NORMAL = easyxf()
BOLD = easyxf('font: bold on')
ROTATED = easyxf('alignment: rotation 90; font: bold on')


def read_excel(filename):

    seating = Bunch()
    workbook = open_workbook(filename)
    for sheet in workbook.sheets():
        if sheet.name == 'Groups':
            _read_groups(seating, sheet)
        elif sheet.name == 'Tables':
            _read_tables(seating, sheet)
        elif sheet.name == 'Seating':
            _read_placement(seating, sheet)
        elif sheet.cell(0, 0).value:
            _read_placement(seating, sheet)
        else:
            _read_groups(seating, sheet)

    return _to_state(seating)


def write_excel(state):
    wb = Workbook(encoding="utf8")

    groups = wb.add_sheet('Groups')
    for person, name in enumerate(state.names):
        groups.write(person + 1, 0, name)
    group_col_count = 1
    for group_name, (i, j), weight in zip(state.group_names, state.group_indexes, state.group_weights):
        if i + 1 == j:
            if weight > 1:
                group_name += " (%d)" % weight
            groups.col(group_col_count).width = 600
            groups.write(0, group_col_count, group_name, style=ROTATED)
            for person in range(state.persons):
                seated = state.seating[person, i]
                if seated:
                    groups.write(person + 1, group_col_count, 1)
            group_col_count += 1

    tables = wb.add_sheet('Tables')
    table_row_count = 0
    for group_name, (i, j), weight in zip(state.group_names, state.group_indexes, state.group_weights):
        if i + 1 < j:
            tables.write(table_row_count, 0, group_name, style=BOLD)
            table_col_count = 1
            for position in range(i, j):
                persons = numpy.where(state.seating[:, position] == 1)[0]
                tables.write(table_row_count, table_col_count, len(persons))
                tables.col(table_col_count).width = 1000
                table_col_count += 1
            table_row_count += 1

    placement = wb.add_sheet('Placement')
    placement_col_count = 0
    for group_name, (i, j), weight in zip(state.group_names, state.group_indexes, state.group_weights):
        if i + 1 < j:
            placement.write(0, placement_col_count, group_name, style=BOLD)
            placement_row_count = 2
            for position in range(i, j):
                persons = numpy.where(state.seating[:, position] == 1)[0]
                for person in persons:
                    fixed = state.fixed[person, position]
                    label = state.names[person]
                    if fixed:
                        label = "*" + label
                    placement.write(placement_row_count, placement_col_count, label, style=BOLD if fixed else NORMAL)
                    placement_row_count += 1
                placement_row_count += 1
            placement_col_count += 1

    result = BytesIO()
    wb.save(result)
    return result.getvalue()


def _read_groups(seating, sheet):

    names = []
    for name in sheet.col(0)[1:]:
        names.append(name.value)

    group_names = []
    for col in range(1, number_of_good_cols(sheet, nrows=1)):
        group_names.append(sheet.cell(0, col).value)

    groups_by_group_name = {group_name: [] for group_name in group_names}

    for row in range(1, number_of_good_rows(sheet, ncols=1)):
        name = sheet.cell(row, 0).value
        for i, group_name in enumerate(group_names):
            if sheet.cell(row, i+1).value:
                groups_by_group_name[group_name].append(name)

    seating.names = names
    seating.groups = [(group_name, groups_by_group_name[group_name]) for group_name in group_names]


def _read_tables(seating, sheet):
    pass


def _read_placement(seating, sheet):

    meals = []
    for col in range(number_of_good_cols(sheet)):
        meal_name = sheet.cell(0, col).value

        positions = []
        position = []
        for cell in sheet.col(col)[1:]:
            name = cell.value
            if name:
                is_fixed = name.startswith('*')
                if is_fixed:
                    name = name[1:]
                position.append([name, is_fixed])
            else:
                if position:
                    positions.append(position)
                position = []
        if position:
            positions.append(position)

        meals.append((meal_name, positions))

    seating.meals = meals


def _to_state(seating):
    group_names = []
    group_weights = []
    group_indexes = []
    cnt = 0

    for meal_name, positions in seating.meals:
        group_names.append(meal_name)
        group_indexes.append((cnt, cnt+len(positions)))
        group_weights.append(1)
        cnt += len(positions)

    for group_name, group in seating.groups:
        group_name, weight_str = re.match(r"\s*(\S*)\s*(?:\((\d+)\))?", group_name).groups()
        if weight_str:
            weight = int(weight_str)
        else:
            weight = 1
        group_names.append(group_name)
        group_indexes.append((cnt, cnt+1))
        group_weights.append(weight)
        cnt += 1

    names = seating.names
    matrix = numpy.zeros((len(names), cnt), dtype=int)
    fixed = numpy.zeros((len(names), cnt), dtype=bool)

    person_index_by_name = {name: i for i, name in enumerate(names)}

    col = 0
    for _, positions in seating.meals:
        for position in positions:
            for name, is_fixed in position:
                row = person_index_by_name[name]
                matrix[row, col] = 1
                fixed[row, col] = is_fixed
            col += 1

    for _, group in seating.groups:
        for name in group:
            row = person_index_by_name[name]
            matrix[row, col] = 1
        col += 1

    geometry = matrix.copy().transpose()

    return State(names=names,
                 group_names=group_names,
                 group_indexes=group_indexes,
                 group_weights=group_weights,
                 seating=matrix,
                 fixed=fixed,
                 geometry=geometry)


def main():
    filename = sys.argv[1] if len(sys.argv) == 2 else "seating.txt"
    if filename.endswith('.xls') or filename.endswith('.xlsx'):
        state = read_excel(filename)
    elif filename.endswith('.txt'):
        state = read_text(filename)
    else:
        state = start_seating()

    # state = optimize(state)

    print dump(state)
    print report(state)
    print repr(state)
    print write_text(state)
    with open("out.xls", "wb") as f:
        f.write(write_excel(state))

if __name__ == '__main__':
    main()
