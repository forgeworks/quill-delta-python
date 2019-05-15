
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

## Setup
If you'd to contribute to quill-delta-python, get started setting your development environment by running:

Checkout the repository

    > git clone https://github.com/forgeworks/quill-delta-python.git

Make sure you have python 3 installed, e.g.,

    > python --version

From inside your new quill-delta-python directory:

    > python3 -m venv env
    > source env/bin/activate
    > pip install poetry
    > poetry install -E html

## Tests
To run tests do:

    > py.test



