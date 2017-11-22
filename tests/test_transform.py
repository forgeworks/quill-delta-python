import pytest
from delta import Delta


def test_insert_and_insert():
    a1 = Delta().insert('A')
    b1 = Delta().insert('B')
    a2 = Delta(a1)
    b2 = Delta(b1)
    
    expected1 = Delta().retain(1).insert('B')
    expected2 = Delta().insert('B')

    assert a1.transform(b1, True) == expected1
    assert a1.transform(b2, False) == expected2


def test_insert_and_retain():
    a = Delta().insert('A')
    b = Delta().retain(1, bold=True, color="red")
    expected = Delta().retain(1).retain(1, bold=True, color="red")
    assert a.transform(b, True) == expected


def test_insert_and_delete():
    a = Delta().insert('A')
    b = Delta().delete(1)
    expected = Delta().retain(1).delete(1)
    assert a.transform(b, True) == expected


def test_delete_and_insert():
    a = Delta().delete(1)
    b = Delta().insert('B')
    expected = Delta().insert('B')
    assert a.transform(b, True) == expected


def test_delete_and_retain():
    a = Delta().delete(1)
    b = Delta().retain(1, bold=True, color='red')
    expected = Delta()
    assert a.transform(b, True) == expected


def test_delete_and_delete():
    a = Delta().delete(1)
    b = Delta().delete(1)
    expected = Delta()
    assert a.transform(b, True) == expected


def test_retain_and_insert():
    a = Delta().retain(1, color='blue')
    b = Delta().insert('B')
    expected = Delta().insert('B')
    assert a.transform(b, True) == expected


def test_retain_and_retain():
    a1 = Delta().retain(1, color='blue')
    b1 = Delta().retain(1, bold=True, color='red')
    a2 = Delta().retain(1, color='blue')
    b2 = Delta().retain(1, bold=True, color='red')
    expected1 = Delta().retain(1, bold=True)
    expected2 = Delta()

    assert a1.transform(b1, True) == expected1
    assert b2.transform(a2, True) == expected2


def test_retain_and_retain_without_priority():
    a1 = Delta().retain(1, color='blue')
    b1 = Delta().retain(1, bold=True, color='red')
    a2 = Delta().retain(1, color='blue')
    b2 = Delta().retain(1, bold=True, color='red')
    expected1 = Delta().retain(1, bold=True, color='red')
    expected2 = Delta().retain(1, color='blue')

    assert a1.transform(b1, False) == expected1
    assert b2.transform(a2, False) == expected2


def test_retain_and_delete():
    a = Delta().retain(1, color='blue')
    b = Delta().delete(1)
    expected = Delta().delete(1)
    assert a.transform(b, True) == expected


def test_alternating_edits():
    a1 = Delta().retain(2).insert('si').delete(5)
    b1 = Delta().retain(1).insert('e').delete(5).retain(1).insert('ow')
    a2 = Delta(a1)
    b2 = Delta(b1)
    expected1 = Delta().retain(1).insert('e').delete(1).retain(2).insert('ow')
    expected2 = Delta().retain(2).insert('si').delete(1)

    assert a1.transform(b1, False) == expected1
    assert b2.transform(a2, False) == expected2


def test_conflicting_appends():
    a1 = Delta().retain(3).insert('aa')
    b1 = Delta().retain(3).insert('bb')
    a2 = Delta(a1)
    b2 = Delta(b1)
    expected1 = Delta().retain(5).insert('bb')
    expected2 = Delta().retain(3).insert('aa')

    assert a1.transform(b1, True) == expected1
    assert b2.transform(a2, False) == expected2


def test_prepend_and_append():
    a1 = Delta().insert('aa')
    b1 = Delta().retain(3).insert('bb')
    expected1 = Delta().retain(5).insert('bb')

    a2 = Delta(a1)
    b2 = Delta(b1)
    expected2 = Delta().insert('aa')

    assert a1.transform(b1, False) == expected1
    assert b2.transform(a2, False) == expected2


def test_trailing_deletes_with_differing_lengths():
    a1 = Delta().retain(2).delete(1)
    b1 = Delta().delete(3)
    expected1 = Delta().delete(2)

    a2 = Delta(a1)
    b2 = Delta(b1)
    expected2 = Delta()

    assert a1.transform(b1, False) == expected1
    assert b2.transform(a2, False) == expected2


def test_immutability():
    a1 = Delta().insert('A')
    a2 = Delta().insert('A')
    b1 = Delta().insert('B')
    b2 = Delta().insert('B')
    expected = Delta().retain(1).insert('B')
    assert a1.transform(b1, True) == expected
    assert a1 == a2
    assert b1 == b2


### Transform Positions ###

def test_insert_before_position():
    delta = Delta().insert('A')
    assert delta.transform(2) == 3

def test_insert_after_position():
    delta = Delta().retain(2).insert('A')
    assert delta.transform(1) == 1

def test_insert_at_position():
    delta = Delta().retain(2).insert('A')
    assert delta.transform(2, True) == 2
    assert delta.transform(2, False) == 3

def test_delete_before_position():
    delta = Delta().delete(2)
    assert delta.transform(4) == 2

def test_delete_after_position():
    delta = Delta().retain(4).delete(2)
    assert delta.transform(2) == 2

def test_delete_across_position():
    delta = Delta().retain(1).delete(4)
    assert delta.transform(2) == 1

def test_insert_and_delete_before_position():
    delta = Delta().retain(2).insert('A').delete(2)
    assert delta.transform(4) == 3

def test_insert_before_and_delete_across_position():
    delta = Delta().retain(2).insert('A').delete(4)
    assert delta.transform(4) == 3

def test_delete_before_and_delete_across_position():
    delta = Delta().delete(1).retain(1).delete(4)
    assert delta.transform(4) == 1



