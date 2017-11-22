


from delta.base import Delta


def test_creation():
    d = Delta()
    d = Delta([])
    d = Delta(d)

    