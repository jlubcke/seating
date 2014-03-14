import sys

import numpy
from seating import State, export, optimize
from xlrd import open_workbook
from xlutils.margins import number_of_good_rows, number_of_good_cols
from bunch import Bunch


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


def read_tables(seating, sheet):
    meals = []
    for col in range(number_of_good_cols(sheet)):
        meal_name = sheet.cell(0, col).value

        tables = []
        table = []
        for cell in sheet.col(col)[1:]:
            value = cell.value
            if value:
                table.append(value)
            else:
                if table != []:
                    tables.append(table)
                table = []
        if table != []:
            tables.append(table)

        meals.append((meal_name, tables))

    seating.meals = meals


def to_state(seating):
    meal_names = []
    meal_indexes = []
    cnt = 0

    for meal_name, tables in seating.meals:
        meal_names.append(meal_name)
        meal_indexes.append((cnt, cnt+len(tables)))
        cnt += len(tables)

    for group_name, group in seating.groups:
        meal_names.append(group_name)
        meal_indexes.append((cnt, cnt+1))
        cnt += 1

    names = seating.names
    matrix = numpy.zeros((len(names), cnt), dtype=int)

    person_index_by_name = {name: i for i, name in enumerate(names)}

    col = 0
    for _, tables in seating.meals:
        for table in tables:
            for name in table:
                row = person_index_by_name[name]
                matrix[row, col] = 1
            col += 1

    for _, group in seating.groups:
        for name in group:
            row = person_index_by_name[name]
            matrix[row, col] = 1
        col += 1

    return State(names=names,
                 meal_names=meal_names,
                 meal_indexes=meal_indexes,
                 seating=matrix,
                 geometry=matrix.transpose())


def read_excel(filename):

    seating = Bunch()
    for sheet in (open_workbook(filename)).sheets():
        if sheet.cell(0, 0).value:
            read_tables(seating, sheet)
        else:
            read_groups(seating, sheet)

    return to_state(seating)


def main():
    filename = sys.argv[1] if len(sys.argv) == 2 else "seating.xlsx"
    state = read_excel(filename)
    state = optimize(state)
    print export(state)


if __name__ == '__main__':
    main()
