import sys
from io import BytesIO

import re
import numpy
from seating import State, optimize, dump, report, start_seating, stats
from text_format import read_text, write_text
from xlrd import open_workbook
from xlutils.margins import number_of_good_rows, number_of_good_cols
from bunch import Bunch
from xlwt import Workbook, easyxf


NORMAL = easyxf()
BOLD = easyxf('font: bold on')
ROTATED = easyxf('alignment: rotation 90; font: bold on')


class ExcelData(object):

    def __init__(self):
        self.names = []
        self.groups = []
        self.dimensions = []
        self.placements = []

def read_excel(file_contents):
    """
    @type file_contents: str
    """
    seating = ExcelData()
    workbook = open_workbook(file_contents=file_contents)
    for sheet in workbook.sheets():
        if sheet.name == 'Groups':
            _read_groups(seating, sheet)
        elif sheet.name == 'Tables':
            _read_tables(seating, sheet)
        elif sheet.name == 'Placement':
            _read_placement(seating, sheet)
        elif sheet.name == 'Statistics':
            continue
        elif sheet.cell(0, 0).value:
            _read_placement(seating, sheet)
        else:
            _read_groups(seating, sheet)

    return _to_state(seating)


def write_excel(state):
    """
    @type state: seating.State
    """
    wb = Workbook(encoding="utf8")

    groups = wb.add_sheet('Groups')
    groups.col(0).width = 7000
    for person, name in enumerate(state.names):
        groups.write(person + 1, 0, name)
    group_col_count = 1
    for group_name, (i, j), weight in zip(state.group_names, state.group_indexes, state.group_weights):
        if weight > 1:
            group_name += " (%d)" % weight
        groups.col(group_col_count).width = 600
        groups.write(0, group_col_count, group_name, style=ROTATED)
        for person in range(state.persons):
            seated = state.seating[person, i:j].any()
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

    statistics = wb.add_sheet('Statistics')
    statistics.write(0, 0, "Pair", style=BOLD)
    statistics.write(0, 1, "Meal closeness", style=BOLD)
    statistics.write(0, 2, "Group closeness", style=BOLD)

    for index, (pair, meal_closeness, group_closeness) in enumerate(stats(state)):
        statistics.write(index + 1, 0, pair)
        statistics.write(index + 1, 1, meal_closeness)
        statistics.write(index + 1, 2, group_closeness)

    result = BytesIO()
    wb.save(result)
    return result.getvalue()


def _read_groups(excel_data, sheet):
    """
    @type excel_data: ExcelData
    @type sheet: xlrd.sheet.Sheet
    """

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

    excel_data.names = names
    excel_data.groups = [(group_name, groups_by_group_name[group_name]) for group_name in group_names]


def _read_tables(excel_data, sheet):
    """
    @type excel_data: ExcelData
    @type sheet: xlrd.sheet.Sheet
    """

    dimensions = []
    for row in range(0, number_of_good_rows(sheet, ncols=1)):
        name = sheet.cell(row, 0).value
        sizes = []
        for col in range(1, number_of_good_cols(sheet)):
            value = sheet.cell(row, col).value
            if value:
                size = int(value)
            else:
                break
            sizes.append(size)
        dimensions.append([name, sizes])
    excel_data.dimensions = dimensions


def _read_placement(excel_data, sheet):
    """
    @type excel_data: ExcelData
    @type sheet: xlrd.sheet.Sheet
    """
    placements = []
    for col in range(number_of_good_cols(sheet)):
        placement_name = sheet.cell(0, col).value

        positions = []
        position = []
        for cell in sheet.col(col)[1:]:
            person = cell.value
            if person:
                is_fixed = person.startswith('*')
                if is_fixed:
                    person = person[1:]
                position.append([person, is_fixed])
            else:
                if position:
                    positions.append(position)
                position = []
        if position:
            positions.append(position)

        placements.append((placement_name, positions))

    excel_data.placements = placements


def _to_state(excel_data):
    """
    @type excel_data: ExcelData
    """
    group_names = []
    group_weights = []
    group_indexes = []

    # Check that placements still respect dimensions constraint
    reset_placement = False
    if excel_data.dimensions is not None:
        for (dimensions_name, sizes), (placement_name, positions) in zip(excel_data.dimensions, excel_data.placements):
            if dimensions_name != placement_name:
                reset_placement = True
                break
            for size, position in zip(sizes, positions):
                if size != len(position):
                    reset_placement = True

    if not reset_placement:
        # Allocate room given placement
        cnt = 0
        for placement_name, positions in excel_data.placements:
            group_names.append(placement_name)
            group_indexes.append([cnt, cnt+len(positions)])
            group_weights.append(1)
            cnt += len(positions)
    else:
        # Allocate room given dimensions
        cnt = 0
        for dimension_name, sizes in excel_data.dimensions:
            group_names.append(dimension_name)
            group_indexes.append([cnt, cnt+len(sizes)])
            group_weights.append(1)
            cnt += len(sizes)

    # Allocate room for groups
    placement_names = set(group_names)
    for group_name, group in excel_data.groups:
        group_name, weight_str = re.match(r"\s*([^(]*)\s*(?:\((\d+)\))?", group_name).groups()
        if weight_str:
            weight = int(weight_str)
        else:
            weight = 1
        if group_name in placement_names:
            continue
        group_names.append(group_name.strip())
        group_indexes.append([cnt, cnt+1])
        group_weights.append(weight)
        cnt += 1

    names = excel_data.names
    matrix = numpy.zeros((len(names), cnt), dtype=int)
    fixed = numpy.zeros((len(names), cnt), dtype=bool)

    person_index_by_name = {name: i for i, name in enumerate(names)}

    if not reset_placement:
        # Fill in positions from placement
        matrix_col = 0
        for _, positions in excel_data.placements:
            for position in positions:
                for person, is_fixed in position:
                    matrix_row = person_index_by_name[person]
                    matrix[matrix_row, matrix_col] = 1
                    fixed[matrix_row, matrix_col] = is_fixed
                matrix_col += 1
    else:
        # Fill in positions in name order
        groups_by_group_name = {group_name: group for group_name, group in excel_data.groups}
        for (i, j), (dimension_name, sizes) in zip(group_indexes, excel_data.dimensions):
            # Traverse names in group with same name (or all persons if there is no such group)
            persons = groups_by_group_name.get(dimension_name, names)
            person_iter = iter(persons)
            try:
                for matrix_col, size in zip(range(i, j), sizes):
                    for _ in range(size):
                        person = next(person_iter)
                        matrix_row = person_index_by_name[person]
                        matrix[matrix_row, matrix_col] = 1
                        fixed[matrix_row, matrix_col] = False
                next(person_iter)
                msg = "Not enough places for all %d persons in '%s' to fit in the given tables." % (len(persons), dimension_name)
                raise Exception(msg)
            except StopIteration:
                pass
        matrix_col = j

    for group_name, group in excel_data.groups:
        if group_name in placement_names:
            continue
        for name in group:
            matrix_row = person_index_by_name[name]
            matrix[matrix_row, matrix_col] = 1
        matrix_col += 1

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
        state = read_excel(open(filename).read())
    elif filename.endswith('.txt'):
        state = read_text(open(filename).read())
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
