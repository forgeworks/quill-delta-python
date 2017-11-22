import pytest
from delta import Delta


def test_insert_and_insert():
    a = Delta().insert('A')
    b = Delta().insert('B')
    expected = Delta().insert('B').insert('A')

    assert a.compose(b) == expected


def test_insert_and_retain():
    a = Delta().insert('A')
    b = Delta().retain(1, bold=True, color='red', font=None)
    expected = Delta().insert('A', bold=True, color='red')

    assert a.compose(b) == expected


def test_insert_and_delete():
    a = Delta().insert('A')
    b = Delta().delete(1)
    expected = Delta()

    assert a.compose(b) == expected


def test_delete_and_insert():
    a = Delta().delete(1)
    b = Delta().insert('B')
    expected = Delta().insert('B').delete(1)

    assert a.compose(b) == expected


def test_delete_and_retain():
    a = Delta().delete(1)
    b = Delta().retain(1, bold=True, color='red')
    expected = Delta().delete(1).retain(1, bold=True, color='red')

    assert a.compose(b) == expected


def test_delete_and_delete():
    a = Delta().delete(1)
    b = Delta().delete(1)
    expected = Delta().delete(2)

    assert a.compose(b) == expected


def test_retain_and_insert():
    a = Delta().retain(1, color='blue')
    b = Delta().insert('B')
    expected = Delta().insert('B').retain(1, color='blue')

    assert a.compose(b) == expected


def test_retain_and_retain():
    a = Delta().retain(1, color='blue')
    b = Delta().retain(1, bold=True, color='red', font=None)
    expected = Delta().retain(1, bold=True, color='red', font=None)

    assert a.compose(b) == expected


def test_retain_and_delete():
    a = Delta().retain(1, color='blue')
    b = Delta().delete(1)
    expected = Delta().delete(1)

    assert a.compose(b) == expected

    
def test_insert_in_middle_of_text():
    a = Delta().insert('Hello')
    b = Delta().retain(3).insert('X')
    expected = Delta().insert('HelXlo')
    
    assert a.compose(b) == expected


def test_insert_and_delete_ordering():
    a = Delta().insert('Hello')
    b = Delta().insert('Hello')
    insertFirst = Delta().retain(3).insert('X').delete(1)
    deleteFirst = Delta().retain(3).delete(1).insert('X')
    expected = Delta().insert('HelXo')

    assert a.compose(insertFirst) == expected
    assert a.compose(deleteFirst) == expected


def test_insert_embed():
    a = Delta().insert(1, src='http://quilljs.com/image.png')
    b = Delta().retain(1, alt='logo')
    expected = Delta().insert(1, src='http://quilljs.com/image.png', alt='logo')
    
    assert a.compose(b) == expected


def test_delete_entire_text():
    a = Delta().retain(4).insert('Hello')
    b = Delta().delete(9)
    expected = Delta().delete(4)

    assert a.compose(b) == expected


def test_retain_more_than_length_of_text():
    a = Delta().insert('Hello')
    b = Delta().retain(10)
    expected = Delta().insert('Hello')

    assert a.compose(b) == expected


def test_retain_empty_embed():
    a = Delta().insert(1)
    b = Delta().retain(1)
    expected = Delta().insert(1)

    assert a.compose(b) == expected


def test_remove_all_attributes():
    a = Delta().insert('A', bold=True)
    b = Delta().retain(1, bold=None)
    expected = Delta().insert('A')

    assert a.compose(b) == expected


def test_remove_all_embed_attributes():
    a = Delta().insert(2, bold=True)
    b = Delta().retain(1, bold=None)
    expected = Delta().insert(2)

    assert a.compose(b) == expected


def test_immutability():
    attr1 = { 'bold': True };
    attr2 = { 'bold': True };
    a1 = Delta().insert('Test', **attr1);
    a2 = Delta().insert('Test', **attr1);
    b1 = Delta().retain(1, color='red').delete(2);
    b2 = Delta().retain(1, color='red').delete(2);
    expected = Delta().insert('T', color='red', bold=True).insert('t', **attr1)
    
    assert a1.compose(b1) == expected
    assert a1 == a2
    assert b1 == b2
    assert attr1 == attr2
