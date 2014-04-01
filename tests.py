from excel_format import write_excel, read_excel
import numpy
from seating import start_seating, dump, State
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


def test_json():
    initial = start_seating()
    json = initial.to_json()
    actual = State.from_json(json)
    _assert_same_state(initial, actual)


def test_excel():
    initial = start_seating()
    excel_content = write_excel(initial)
    actual = read_excel(excel_content)
    _assert_same_state(initial, actual)


def test_text_format():
    initial = start_seating()
    text_content = write_text(initial)
    actual = read_text(text_content)
    _assert_same_state(initial, actual)
