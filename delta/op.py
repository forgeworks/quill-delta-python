import copy


def compose(a, b, keep_null=False):
    """
    Compose two operations into one.

    ``keep_null`` [default=false] is a boolean that controls whether None/Null 
    attributes are retrained.
    """
    if a is None:
        a = {}
    if b is None:
        b = {}

    # deep copy b, but get rid of None values if keep_null is falsey
    attributes = dict((k, copy.deepcopy(v)) for k, v in b.items() if keep_null or v is not None)

    for k, v in a.items():
        if k not in b:
            attributes[k] = copy.deepcopy(v)

    return attributes or None


def diff(a, b):
    """
    Return the difference between operations a and b.
    """
    if a is None:
        a = {}
    if b is None:
        b = {}

    keys = set(a.keys()).union(set(b.keys()))

    attributes = {}
    for k in keys:
        av, bv = a.get(k, None), b.get(k, None)
        if av != bv:
            attributes[k] = bv

    return attributes or None


def transform(a, b, priority=True):
    """
    Return the transformation from operation a to b.

    If ``priority`` is falsey [default=True] then just return b.
    """
    if a is None:
        a = {}
    if b is None:
        b = {}

    if not priority:
        return b or None
    
    attributes = {}
    for k, v in b.items():
        if k not in a:
            attributes[k] = v

    return attributes or None


def length_of(op):
    typ = type_of(op)
    if typ == 'delete':
        return op['delete']
    elif typ == 'retain':
        return op['retain']
    elif isinstance(op.get('insert'), str):
        return len(op['insert'])
    else:
        return 1


def type_of(op):
    if not op:
        return None
    if isinstance(op.get('delete'), int):
        return 'delete'
    if isinstance(op.get('retain'), int):
        return 'retain'
    return 'insert'





class Iterator(object):
    """
    An iterator that enables itself to break off operations
    to exactly the length needed via the ``next()`` method.
    """
    def __init__(self, ops=[]):
        self.ops = ops
        self.reset()

    def reset(self):
        self.index = 0
        self.offset = 0

    def has_next(self):
        return self.peek_length() is not None

    def next(self, length=None):
        offset = self.offset

        op = self.peek()
        op_type = type_of(op)
        if op is None:
            return { 'retain': None }
        
        op_length = length_of(op)
        if (length is None or length >= op_length - offset):
            length = op_length - offset
            self.index += 1
            self.offset = 0
        else:
            self.offset += length

        if op_type == 'delete':
            return { 'delete': length }

        result_op = {}
        if op.get('attributes'):
            result_op['attributes'] = op['attributes']

        if op_type == 'retain':
            result_op['retain'] = length
        elif isinstance(op.get('insert'), str):
            result_op['insert'] = op['insert'][offset:offset+length]
        else:
            assert offset == 0
            assert length == 1
            if 'insert' in op:
                result_op['insert'] = op['insert']

        return result_op

    __next__ = next

    def __length__(self):
        return len(self.ops)

    def __iter__(self):
        return self

    def peek(self):
        try:
            return self.ops[self.index]
        except IndexError:
            return None

    def peek_length(self):
        next_op = self.peek()
        if next_op is None:
            return None
        return length_of(next_op) - self.offset

    def peek_type(self):
        op = self.peek()
        if op is None:
            return 'retain'
        return type_of(op)

length = length_of
type = type_of
iterator = lambda x: Iterator(x)