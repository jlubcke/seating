from io import BytesIO
from excel_format import write_excel, read_excel
import numpy
import pytest
from seating import start_seating, dump, State, TablePositionAgnosticClosnessEvaluator, SingleThreadedSearcher, \
    ClosenessStepper, SquareStateEvaluator, PrintLogger, report
from text_format import write_text, read_text
from xlrd import open_workbook
from xlutils.copy import copy


def _assert_same_state(expected, actual):
    for key in expected:
        if isinstance(expected[key], (numpy.ndarray, numpy.generic)):
            assert numpy.array_equal(expected[key], actual[key]), "%s: %s != %s" % (key, expected[key], actual[key])
        else:
            assert expected[key] == actual[key]


def test_swap():
    initial = start_seating(persons=2, meals=3, positions=2, groups=0)

    state = initial.copy()
    assert dump(initial) == dump(state)
    state.swap(2, 4, 0, 1)
    assert dump(initial) != dump(state)
    state.swap(2, 4, 0, 1)
    assert dump(initial) == dump(state)
    _assert_same_state(initial, state)
    assert initial == state
    assert not initial != state


def test_optimize():
    initial = start_seating()
    evaluator = TablePositionAgnosticClosnessEvaluator()
    searcher = SingleThreadedSearcher(
        ClosenessStepper(evaluator),
        SquareStateEvaluator(evaluator),
        PrintLogger()
    )
    state, e1 = searcher.search(initial, n=1)
    _, e2 = searcher.search(initial, n=100)
    assert e2 < e1


def _explicit_initial():
    return read_text("""
# Meal 1

Alice

*Bob
Charlie

# Meal 2

Alice
Bob

Charlie

# Meal 3

Charlie
Dave

# Group 1 (17)

Alice
Bob

# Group 2 (42)

Charlie
Dave
""")


@pytest.fixture(params=[start_seating(),
                        _explicit_initial()])
def initial(request):
    return request.param


def test_json(initial):
    json = initial.to_json()
    actual = State.from_json(json)
    _assert_same_state(initial, actual)


def test_excel(initial):
    excel_content = write_excel(initial)
    actual = read_excel(excel_content)
    _assert_same_state(initial, actual)


def test_text_format(initial):
    text_content = write_text(initial)
    actual = read_text(text_content)
    print repr(actual)
    _assert_same_state(initial, actual)


def test_excel_change_geometry():

    start_state = read_text("""\
# Meal #0
3
2

1
0

# Meal #1
3
2

1
0
# Meal #2
2
1

0
""")

    assert dump(start_state) == """\
# Meal #0
   [2 3]
   [0 1]
# Meal #1
   [2 3]
   [0 1]
# Meal #2
   [1 2]
   [0]
"""

    rb = open_workbook(file_contents=(write_excel(start_state)))

    assert int(rb.sheet_by_index(1).cell(0, 1).value) == 2

    wb = copy(rb)
    wb.get_sheet(1).write(0, 1, 3)
    result = BytesIO()
    wb.save(result)
    new_state = read_excel(result.getvalue())

    assert dump(new_state) == """\
# Meal #0
   [0 1 2]
   [3]
# Meal #1
   [0 1]
   [2 3]
# Meal #2
   [0 1]
   [2]
"""


def test_report():
    state = read_text("""\
# Foo
1
2

3
4

#Bar
1
3

2
4

# Odd (17)
1
3

# Even (42)
2
4
""")

    assert report(state) == """\
Foo
  0
    Odd: 1
    Even: 1
  1
    Odd: 1
    Even: 1
Bar
  0
    Odd: 2
  1
    Even: 2
"""
