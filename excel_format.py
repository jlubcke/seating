import sys
from io import BytesIO

import numpy
from seating import State, export, optimize, parse, dump
from xlrd import open_workbook
from xlutils.margins import number_of_good_rows, number_of_good_cols
from bunch import Bunch
from xlwt import Workbook, easyxf


def read_groups(seating, sheet):

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


def read_tables(seating, workbook, sheet):

    meals = []
    for col in range(number_of_good_cols(sheet)):
        meal_name = sheet.cell(0, col).value

        tables = []
        table = []
        for cell in sheet.col(col)[1:]:
            value = cell.value
            if value:
                fixed = value.startswith('*')
                if fixed:
                    value = value[1:]
                table.append([value, fixed])
            else:
                if table:
                    tables.append(table)
                table = []
        if table:
            tables.append(table)

        meals.append((meal_name, tables))

    seating.meals = meals


def to_state(seating):
    group_names = []
    group_indexes = []
    cnt = 0

    for meal_name, tables in seating.meals:
        group_names.append(meal_name)
        group_indexes.append((cnt, cnt+len(tables)))
        cnt += len(tables)

    for group_name, group in seating.groups:
        group_names.append(group_name)
        group_indexes.append((cnt, cnt+1))
        cnt += 1

    names = seating.names
    matrix = numpy.zeros((len(names), cnt), dtype=int)
    fixed = numpy.zeros((len(names), cnt), dtype=bool)

    person_index_by_name = {name: i for i, name in enumerate(names)}

    col = 0
    for _, tables in seating.meals:
        for table in tables:
            for name, is_bold in table:
                row = person_index_by_name[name]
                matrix[row, col] = 1
                fixed[row, col] = is_bold
            col += 1

    for _, group in seating.groups:
        for name in group:
            row = person_index_by_name[name]
            matrix[row, col] = 1
        col += 1

    return State(names=names,
                 group_names=group_names,
                 group_indexes=group_indexes,
                 seating=matrix,
                 fixed=fixed,
                 geometry=matrix.copy().transpose())


def read_excel(filename):

    seating = Bunch()
    workbook = open_workbook(filename)
    for sheet in (workbook).sheets():
        if sheet.cell(0, 0).value:
            read_tables(seating, workbook, sheet)
        else:
            read_groups(seating, sheet)

    return to_state(seating)


NORMAL = easyxf()
BOLD = easyxf('font: bold on')


def write_excel(state):
    wb = Workbook(encoding="utf8")

    meals = wb.add_sheet('Meals')
    groups = wb.add_sheet('Groups')

    meal_col_count = 0
    group_col_count = 1
    for p, name in enumerate(state.names):
        groups.write(p + 1, 0, name)

    for meal_name, (i, j) in zip(state.group_names, state.group_indexes):
        if i + 1 == j:
            groups.write(0, group_col_count, meal_name, style=BOLD)
            for p in range(state.persons):
                seated = state.seating[p, i]
                if seated:
                    groups.write(p + 1, group_col_count, 1)
            group_col_count += 1

        else:
            meals.write(0, meal_col_count, meal_name, style=BOLD)
            meal_row_count = 2
            for table in range(j-i):
                for p in numpy.where(state.seating[:, i+table] == 1)[0]:
                    fixed = state.fixed[p, i+table]
                    label = state.names[p]
                    if fixed:
                        label = "*" + label
                    meals.write(meal_row_count, meal_col_count, label, style=BOLD if fixed else NORMAL)
                    meal_row_count += 1
                meal_row_count += 1

            meal_col_count += 1

    result = BytesIO()
    wb.save(result)
    return result.getvalue()


def main():
    filename = sys.argv[1] if len(sys.argv) == 2 else "seating.txt"
    if filename.endswith('.xls') or filename.endswith('.xlsx'):
        state = read_excel(filename)
    if filename.endswith('.txt'):
        state = parse(filename)

    state = optimize(state)

    print export(state)
    with open("out.xls", "wb") as f:
        f.write(write_excel(state))

if __name__ == '__main__':
    main()
