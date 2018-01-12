import copy
import diff_match_patch

try:
    from functools import reduce
except:
    pass

from . import op


NULL_CHARACTER = chr(0)
DIFF_EQUAL = 0
DIFF_INSERT = 1
DIFF_DELETE = -1


def merge(a, b):
    return copy.deepcopy(a or {}).update(b or {})

def differ(a, b, timeout=1):
    differ = diff_match_patch.diff_match_patch()
    differ.Diff_Timeout = timeout
    return differ.diff_main(a, b)

def smallest(*parts):
    return min(filter(lambda x: x is not None, parts))


class Delta(object):
    def __init__(self, ops=None, **attrs):
        if hasattr(ops, 'ops'):
            ops = ops.ops
        self.ops = ops or []
        self.__dict__.update(attrs)

    def __eq__(self, other):
        return self.ops == other.ops

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.ops)

    def insert(self, text, **attrs):
        if text == "":
            return self
        new_op = {'insert': text}
        if attrs:
            new_op['attributes'] = attrs
        return self.push(new_op)

    def delete(self, length):
        if length <= 0:
            return self
        return self.push({'delete': length});

    def retain(self, length, **attrs):
        if length <= 0:
            return self
        new_op = {'retain': length}
        if attrs:
            new_op['attributes'] = attrs
        return self.push(new_op)

    def push(self, operation):
        index = len(self.ops)
        new_op = copy.deepcopy(operation)
        try:
            last_op = self.ops[index - 1]
        except IndexError:
            self.ops.append(new_op)
            return self
        
        if op.type(new_op) == op.type(last_op) == 'delete':
            last_op['delete'] += new_op['delete']
            return self

        if op.type(last_op) == 'delete' and op.type(new_op) == 'insert':
            index -= 1
            try:
                last_op = self.ops[index - 1]
            except IndexError:
                self.ops.insert(0, new_op)
                return self

        if new_op.get('attributes') == last_op.get('attributes'):
            if isinstance(new_op.get('insert'), str) and isinstance(last_op.get('insert'), str):
                last_op['insert'] += new_op['insert']
                return self

            if isinstance(new_op.get('retain'), int) and isinstance(last_op.get('retain'), int):
                last_op['retain'] += new_op['retain']
                return self

        self.ops.insert(index, new_op)
        return self

    def extend(self, ops):
        if hasattr(ops, 'ops'):
            ops = ops.ops
        if not ops:
            return self
        self.push(ops[0])
        self.ops.extend(ops[1:])
        return self

    def concat(self, other):
        delta = self.__class__(copy.deepcopy(self.ops))
        delta.extend(other)
        return delta

    def chop(self):
        try:
            last_op = self.ops[-1]
            if op.type(last_op) == 'retain' and not last_op.get('attributes'):
                self.ops.pop()
        except IndexError:
            pass
        return self

    def document(self):
        parts = []
        for op in self:
            insert = op.get('insert')
            if insert:
                if isinstance(insert, str):
                    parts.append(insert)
                else:
                    parts.append(NULL_CHARACTER)
            else:
                raise ValueError("document() can only be called on Deltas that have only insert ops")
        return "".join(parts)

    def __iter__(self):
        return iter(self.ops)

    def __getitem__(self, index):
        if isinstance(index, int):
            start = index
            stop = index + 1

        elif isinstance(index, slice):
            start = index.start or 0
            stop = index.stop or None

            if index.step is not None:
                print(index)
                raise ValueError("no support for step slices")

        if (start is not None and start < 0) or (stop is not None and stop < 0):
            raise ValueError("no support for negative indexing.")

        ops = []
        iter = self.iterator()
        index = 0
        while iter.has_next():
            if stop is not None and index >= stop:
                break
            if index < start:
                next_op = iter.next(start - index)
            else:
                if stop is not None:
                    next_op = iter.next(stop-index)
                else:
                    next_op = iter.next()
                ops.append(next_op)
            index += op.length(next_op)

        return Delta(ops)

    def __len__(self):
        return sum(op.length(o) for o in self.ops)

    def iterator(self):
        return op.iterator(self.ops)

    def change_length(self):
        length = 0
        for operator in self:
            if op.type(operator) == 'delete':
                length -= operator['delete']
            else:
                length += op.length(operator)
        return length

    def length(self):
        return sum(op.length(o) for o in self)

    def compose(self, other):
        self_it = self.iterator()
        other_it = other.iterator()
        delta = self.__class__()
        while self_it.has_next() or other_it.has_next():
            if other_it.peek_type() == 'insert':
                delta.push(other_it.next())
            elif self_it.peek_type() == 'delete':
                delta.push(self_it.next())
            else:
                length = smallest(self_it.peek_length(), other_it.peek_length())
                self_op = self_it.next(length)
                other_op = other_it.next(length)
                if 'retain' in other_op:
                    new_op = {}
                    if 'retain' in self_op:
                        new_op['retain'] = length
                    elif 'insert' in self_op:
                        new_op['insert'] = self_op['insert']
                    # Preserve null when composing with a retain, otherwise remove it for inserts
                    attributes = op.compose(self_op.get('attributes'), other_op.get('attributes'), isinstance(self_op.get('retain'), int))
                    if (attributes):
                        new_op['attributes'] = attributes
                    delta.push(new_op)
                # Other op should be delete, we could be an insert or retain
                # Insert + delete cancels out
                elif op.type(other_op) == 'delete' and 'retain' in self_op:
                    delta.push(other_op)
        return delta.chop()
    
    def diff(self, other):
        """
        Returns a diff of two *documents*, which is defined as a delta
        with only inserts. 
        """
        if self.ops == other.ops:
            return self.__class__()
        
        self_doc = self.document()
        other_doc = other.document()
        self_it = self.iterator()
        other_it = other.iterator()
        
        delta = self.__class__()
        for code, text in differ(self_doc, other_doc):
            length = len(text)
            while length > 0:
                op_length = 0
                if code == DIFF_INSERT:
                    op_length = min(other_it.peek_length(), length)
                    delta.push(other_it.next(op_length))
                elif code == DIFF_DELETE:
                    op_length = min(length, self_it.peek_length())
                    self_it.next(op_length)
                    delta.delete(op_length)
                elif code == DIFF_EQUAL:
                    op_length = min(self_it.peek_length(), other_it.peek_length(), length)
                    self_op = self_it.next(op_length)
                    other_op = other_it.next(op_length)
                    if self_op.get('insert') == other_op.get('insert'):
                        attributes = op.diff(self_op.get('attributes'), other_op.get('attributes'))
                        delta.retain(op_length, **(attributes or {}))
                    else:
                        delta.push(other_op).delete(op_length)
                else:
                    raise RuntimeError("Diff library returned unknown op code: %r", code)
                if op_length == 0:
                    return
                length -= op_length
        return delta.chop()

    def each_line(self, fn, newline='\n'):
        for line, attributes, index in self.iter_lines():
            if fn(line, attributes, index) is False:
                break

    def iter_lines(self, newline='\n'):
        iter = self.iterator()
        line = self.__class__()
        i = 0
        while iter.has_next():
            if iter.peek_type() != 'insert':
                return
            self_op = iter.peek()
            start = op.length(self_op) - iter.peek_length()
            if isinstance(self_op.get('insert'), str):
                index = self_op['insert'][start:].find(newline)
            else:
                index = -1
            
            if index < 0:
                line.push(iter.next())
            elif index > 0:
                line.push(iter.next(index))
            else:
                yield line, iter.next(1).get('attributes', {}), i
                i += 1
                line = Delta()
        if len(line) > 0:
            yield line, {}, i

    def transform(self, other, priority=False):
        if isinstance(other, int):
            return self.transform_position(other, priority)

        self_it = self.iterator()
        other_it = other.iterator()
        delta = Delta()

        while self_it.has_next() or other_it.has_next():
            if self_it.peek_type() == 'insert' and (priority or other_it.peek_type() != 'insert'):
                delta.retain(op.length(self_it.next()))
            elif other_it.peek_type() == 'insert':
                delta.push(other_it.next())
            else:
                length = smallest(self_it.peek_length(), other_it.peek_length())
                self_op = self_it.next(length)
                other_op = other_it.next(length)
                if self_op.get('delete'):
                    # Our delete either makes their delete redundant or removes their retain
                    continue
                elif other_op.get('delete'):
                    delta.push(other_op)
                else:
                    # We retain either their retain or insert
                    delta.retain(length, **(op.transform(self_op.get('attributes'), other_op.get('attributes'), priority) or {}))

        return delta.chop()

    def transform_position(self, index, priority=False):
        iter = self.iterator()
        offset = 0
        while iter.has_next() and offset <= index:
            length = iter.peek_length()
            next_type = iter.peek_type()
            iter.next()
            if next_type == 'delete':
                index -= min(length, index - offset)
                continue
            elif next_type == 'insert' and (offset < index or not priority):
                index += length
            offset += length
        return index
