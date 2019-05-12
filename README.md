
# Delta (Python Port)

Python port of the javascript Delta library for QuillJS: https://github.com/quilljs/delta

Some basic pythonizing has been done, but mostly it works exactly like the above library.

There is no other python specific documentation at this time, sorry.  Please see the tests
for reference examples.

## Install with [Poetry](https://poetry.eustace.io/docs/#installation)

With HTML rendering:

    > poetry add -E html quill-delta

Without HTML rendering:

    > poetry add quill-delta

## Install with pip

Note: If you're using `zsh`, see below.

With HTML rendering:

    > pip install quill-delta[html]

With HTML rendering (zsh):

    > pip install quill-delta"[html]"

Without HTML rendering:

    > pip install quill-delta


# Rendering HTML in Python

This library includes a module `delta.html` that renders html from an operation list,
allowing you to render Quill Delta operations in full from a Python server.

For example:

    from delta import html

    ops = [ 
        { "insert":"Quill\nEditor\n\n" },
        { "insert": "bold",
          "attributes": {"bold": True}},
        { "insert":" and the " },
        { "insert":"italic",
          "attributes": { "italic": True }},
        { "insert":"\n\nNormal\n" },
    ]

    html.render(ops)

Result (line formatting added for readability):
    
    <p>Quill</p>
    <p>Editor</p>
    <p><br></p>
    <p><strong>bold</strong> and the <em>italic</em></p>
    <p><br></p>
    <p>Normal</p>

[See test_html.py](tests/test_html.py) for more examples.


# Developing

## Tests

    > py.test


