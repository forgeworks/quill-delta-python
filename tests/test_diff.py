import pytest
from delta import Delta


def test_insert():
    a = Delta()
    a.insert('A')

    b = Delta()
    b.insert('AB')

    expected = Delta().retain(1).insert('B')
    assert a.diff(b) == expected


def test_delete():
    a = Delta()
    a.insert('AB')

    b = Delta()
    b.insert('A')

    expected = Delta().retain(1).delete(1)
    assert a.diff(b) == expected


def test_retain():
    a = Delta()
    a.insert('A')

    b = Delta()
    b.insert('A')

    expected = Delta()
    assert a.diff(b) == expected


def test_format():
    a = Delta()
    a.insert('A')

    b = Delta()
    b.insert('A', bold=True)

    expected = Delta().retain(1, bold=True)
    assert a.diff(b) == expected


def test_attributes():
    a = Delta().insert('A', font={'family': 'Helvetica', 'size': '15px'})
    b = Delta().insert('A', font={'family': 'Helvetica', 'size': '15px'})

    assert a.diff(b) == Delta()


def test_embed():
    # Same
    a = Delta().insert(1)
    b = Delta().insert(1)
    assert a.diff(b) == Delta()

    # Different
    a = Delta().insert(1)
    b = Delta().insert(2)
    assert a.diff(b) == Delta().delete(1).insert(2)

    # Object
    a = Delta().insert({ 'image': 'http://quilljs.com' })
    b = Delta().insert({ 'image': 'http://quilljs.com' })
    assert a.diff(b) == Delta()

    # Different Object
    a = Delta().insert({ 'image': 'http://quilljs.com', 'alt': 'Overwrite' })
    b = Delta().insert({ 'image': 'http://quilljs.com' })
    assert a.diff(b) == Delta().delete(1).insert({ 'image': 'http://quilljs.com' })

    # Object change
    embed = { 'image': 'http://quilljs.com' }
    a = Delta().insert(embed)
    embed['image'] = "http://github.com"
    b = Delta().insert(embed)
    expected = Delta().insert({ 'image': 'http://github.com' }).delete(1)
    assert a.diff(b) == expected

    # False Positive
    a = Delta().insert(1)
    b = Delta().insert(chr(0))  #Placeholder char for embed
    expected = Delta().insert(chr(0)).delete(1)


def test_document():
    a = Delta().insert("AB").insert("C")
    assert a.document() == "ABC"

    with pytest.raises(ValueError):
        Delta().retain(1).insert('B').document()


def test_inconvenient_indexes():
    a = Delta().insert('12', bold=True).insert('34', italic=True)
    b = Delta().insert('123', color="red")
    expected = Delta().retain(2, bold=None, color="red").retain(1, italic=None, color="red").delete(1)
    assert a.diff(b) == expected


def test_combination():
    a = Delta().insert('Bad', color='red').insert('cat', color='blue')
    b = Delta().insert('Good', bold=True).insert('dog', italic=True)
    expected = Delta() \
                    .insert('Good', bold=True) \
                    .delete(2) \
                    .retain(1, italic=True, color=None) \
                    .delete(3) \
                    .insert('og', italic=True)
    print(a.document(), b.document(), expected)
    assert a.diff(b) == expected


def test_same_document():
    a = Delta().insert('A').insert('B', bold=True)
    expected = Delta()
    assert a.diff(a) == expected


def test_immutability():
    attr1 = { 'color': 'red' };
    attr2 = { 'color': 'red' };
    a1 = Delta().insert('A', **attr1);
    a2 = Delta().insert('A', **attr1);
    b1 = Delta().insert('A', bold=True).insert('B');
    b2 = Delta().insert('A', bold=True).insert('B');
    
    expected = Delta().retain(1, bold=True, color=None).insert('B');

    assert a1.diff(b1) == expected;
    assert a1 == a2
    assert b2 == b2
    assert attr1 == attr2


    