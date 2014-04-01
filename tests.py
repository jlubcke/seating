from excel_format import write_excel, read_excel
import numpy
import pytest
from seating import start_seating, dump, State, optimize, TablePositionAgnosticClosnessEvaluator, SingleThreadedSearcher, \
    ClosenessStepper, SquareStateEvaluator, PrintLogger
from text_format import write_text, read_text


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

Bob
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
    _assert_same_state(initial, actual)
