import json
from delta import Delta
try:
    import mock
except ImportError:
    from unittest import mock


def get_args(mock, index):
    args, kwargs = mock.call_args_list[index]
    return args


def test_each_line():
    # Expected
    delta = Delta().insert('Hello\n\n') \
                   .insert('World', bold=True) \
                   .insert({ 'image': 'octocat.png' }) \
                   .insert('\n', align='right') \
                   .insert('!')

    fn = mock.Mock()
    delta.each_line(fn)

    assert fn.call_count == 4
    assert get_args(fn, 0) == (Delta().insert('Hello'), {}, 0)
    assert get_args(fn, 1) == (Delta(), {}, 1)
    assert get_args(fn, 2) == (Delta().insert('World', bold=True).insert({ 'image': 'octocat.png' }),
                               {'align': 'right'},
                               2)
    assert get_args(fn, 3) == ( Delta().insert('!'), {}, 3 )


    # Trailing newline
    delta = Delta().insert('Hello\nWorld!\n')
    fn = mock.Mock()

    delta.each_line(fn)
    assert fn.call_count == 2
    assert get_args(fn, 0) == (Delta().insert("Hello"), {}, 0)
    assert get_args(fn, 1) == (Delta().insert("World!"), {}, 1)


    # Non Document
    delta = Delta().retain(1).delete(2)
    fn = mock.Mock()
    
    delta.each_line(fn);
    assert fn.call_count == 0


    # Early Return
    state = {'count': 0}
    def counter(*args):
        if state['count'] == 1:
            return False
        state['count'] += 1

    delta = Delta().insert('Hello\nNew\nWorld!')
    fn = mock.Mock(side_effect=counter)
    
    delta.each_line(fn)
    assert fn.call_count == 2


def test_concat():
    # empty delta
    delta = Delta().insert('Test')
    concat = Delta()
    expected = Delta().insert('Test')

    assert delta.concat(concat) == expected

    # unmergeable
    delta = Delta().insert('Test')
    original = Delta(delta.ops)
    concat = Delta().insert('!', bold=True)
    expected = Delta().insert('Test').insert('!', bold=True)
    
    assert delta.concat(concat) == expected
    assert delta == original

    # mergeable
    delta = Delta().insert('Test', bold=True)
    original = Delta(delta.ops)
    concat = Delta().insert('!', bold=True).insert('\n')
    expected = Delta().insert('Test!', bold=True).insert('\n')

    assert delta.concat(concat) == expected
    assert delta == original


def test_slice():
    # start
    delta = Delta().retain(2).insert('A')
    expected = Delta().insert('A')
    
    assert delta[2:] == expected

    # end
    delta = Delta().retain(2).insert('A')
    expected = Delta().retain(2)
    
    assert delta[:2] == expected

    # start and end chop
    delta = Delta().insert('0123456789')
    expected = Delta().insert('23456')
    
    assert delta[2:7] == expected

    # start and end multiple chop
    delta = Delta().insert('0123', bold=True).insert('4567')
    expected = Delta().insert('3', bold=True).insert('4')

    assert delta[3:5] == expected

    # start and end
    delta = Delta().retain(2).insert('A', bold=True).insert('B')
    expected = Delta().insert('A', bold=True)

    assert delta[2:3] == expected

    # no params
    delta = Delta().retain(2).insert('A', bold=True).insert('B')

    assert delta[:] == delta

    # split ops
    delta = Delta().insert('AB', bold=True).insert('C')
    expected = Delta().insert('B', bold=True)

    assert delta[1:2] == expected

    # split ops multiple times
    delta = Delta().insert('ABC', bold=True).insert('D')
    expected = Delta().insert('B', bold=True)

    assert delta[1:2] == expected

    # Single
    delta = Delta().insert('ABC', bold=True)
    assert delta[0] == Delta().insert('A', bold=True)


def test_chop():
    # Retain
    a = Delta().insert('Test').retain(4)
    expected = Delta().insert('Test')

    assert a.chop() == expected

    # Insert
    a = Delta().insert('Test')
    expected = Delta().insert('Test')

    assert a.chop() == expected

    # Formatted
    a = Delta().insert('Test').retain(4, bold=True)
    expected = Delta().insert('Test').retain(4, bold=True)

    assert a.chop() == expected


def test_length():
    assert len(Delta().insert('Test')) == 4
    assert len(Delta().insert(1)) == 1
    assert len(Delta().retain(2)) == 2
    assert len(Delta().retain(2).delete(1)) == 3
