from delta import op


def test_length():
    assert op.length({'delete': 5}) == 5
    assert op.length({'retain': 4}) == 4
    assert op.length({'insert': 'python'}) == 6
    assert op.length({'insert': 2}) == 1

def test_type():
    assert op.type({'delete': 5}) == 'delete'
    assert op.type({'retain': 5}) == 'retain'
    assert op.type({'insert': 'text'}) == 'insert'
    assert op.type({'insert': 1}) == 'insert'
    assert op.type({}) == None


def test_compose():
    attributes = { 'bold': True, 'color': 'red' }

    assert op.compose(None, attributes) == attributes
    assert op.compose(attributes, None) == attributes
    assert op.compose(None, None) is None

    assert op.compose(attributes, {'italic': True}) == { 'bold': True, 'color': 'red', 'italic': True }
    assert op.compose(attributes, {'color': 'blue', 'bold': False}) == { 'bold': False, 'color': 'blue' }
    assert op.compose(attributes, {'bold': None}) == { 'color': 'red' }

    assert op.compose(attributes, {'bold': None, 'color': None}) is None
    assert op.compose(attributes, {'italic': None}) == attributes

def test_diff():
    format = { 'bold': True, 'color': 'red' }

    assert op.diff(None, format) == format
    assert op.diff(format, None) == {'bold': None, 'color': None}
    assert op.diff(format, format) == None

    assert op.diff(format, { 'bold': True, 'italic': True, 'color': 'red' }) == {'italic': True}
    assert op.diff(format, { 'bold': True }) == {'color': None}
    assert op.diff(format, { 'bold': True, 'color': 'blue' }) == {'color': 'blue'}

def test_transform():
    left = { 'bold': True, 'color': 'red', 'font': None }
    right = { 'color': 'blue', 'font': 'serif', 'italic': True };

    assert op.transform(None, left, False) == left
    assert op.transform(left, None, False) is None
    assert op.transform(None, None, False) is None

    assert op.transform(left, right, True) == {'italic': True}
    assert op.transform(left, right, False) == right


def test_iterator():
    ops = [
        {'insert': 'Hello', 'attributes': {'bold': True}},
        {'retain': 3},
        {'insert': 2, 'attributes': {'src': 'http://quilljs.com/'}},
        {'delete': 4},
    ]

    iterator = op.iterator(ops)
    assert iterator.offset == 0
    assert iterator.index == 0
    assert iterator.ops == ops

    assert iterator.has_next()
    assert iterator.peek() == {'insert': 'Hello', 'attributes': {'bold': True}}
    assert iterator.peek_length() == 5
    assert iterator.peek_type() == 'insert'

    iterator.next()
    assert iterator.peek_type() == 'retain'
    assert iterator.peek_length() == 3

    iterator.next()
    assert iterator.peek_type() == 'insert'
    assert iterator.peek_length() == 1

    iterator.next()
    assert iterator.peek_type() == 'delete'
    assert iterator.peek_length() == 4

    for i in range(10):
        iterator.next()
        assert iterator.peek_type() == 'retain'
        assert iterator.peek_length() is None

    iterator.reset()
    for operator, next in zip(ops, iterator):
        assert operator == next


def test_iterator_next_length():
    ops = [
        {'insert': 'Hello', 'attributes': {'bold': True}},
        {'retain': 3},
        {'insert': 2, 'attributes': {'src': 'http://quilljs.com/'}},
        {'delete': 4},
    ]

    iterator = op.iterator(ops)
    iterator.next(2)
    assert iterator.peek_length() == 5 - 2

    assert iterator.next(2)['insert'] == 'll'
    assert iterator.next()['insert'] == 'o'
    
    assert iterator.next()['retain']
    assert iterator.next()['insert']
    assert iterator.next()['delete']

    for i in range(10):
        assert iterator.next()['retain'] is None


def test_empty_iterator():
    iterator = op.iterator([])
    assert iterator.offset == 0
    assert iterator.index == 0
    assert iterator.ops == []
    assert iterator.has_next() is False
    assert iterator.peek() is None
    assert iterator.peek_length() is None
    assert iterator.peek_type() is 'retain'


def test_next():
    ops = [
        {'insert': 'Bad'},
        {'insert': 'cat'},
    ]

    iterator = op.iterator(ops)
    iterator.next(2)
    iterator.next(1)
    assert iterator.index == 1
    assert iterator.peek() == ops[1]
    