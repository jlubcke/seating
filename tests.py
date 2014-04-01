from excel_format import write_excel, read_excel
import numpy
from seating import start_seating, dump, State
from text_format import write_text, read_text


def test_swap():
    state = start_seating(persons=2, meals=3, positions=2, groups=0)

    print dump(state)
    print state.seating
    print state.swap(2, 4, 0, 1)
    print dump(state)
    print state.seating


def test_json():
    initial = start_seating()
    json = initial.to_json()
    actual = State.from_json(json)

    assert dump(initial) == dump(actual)

    _check_state(initial, actual)


def _check_state(expected, actual):
    print expected.group_names
    print actual.group_names
    print expected.group_indexes
    print actual.group_indexes
    print dump(expected)
    print dump(actual)
    for key in expected:
        if isinstance(expected[key], (numpy.ndarray, numpy.generic)):
            assert numpy.array_equal(expected[key], actual[key]), "%s: %s != %s" % (key, expected[key], actual[key])
        else:
            assert expected[key] == actual[key]


def test_excel():
    initial = start_seating(persons=2, meals=3, positions=2, groups=3)

    excel_content = write_excel(initial)
    actual = read_excel(excel_content)
    _check_state(initial, actual)


def test_text_format():
    initial = start_seating(persons=2, meals=3, positions=2, groups=3)
    text_content = write_text(initial)
    print text_content
    actual = read_text(text_content)
    _check_state(initial, actual)
