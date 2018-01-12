from delta import html
from delta.base import Delta

def test_basics():
    ops = [ 
        { "insert":"Quill\nEditor\n\n" },
        { "insert": "bold",
          "attributes": {"bold": True}},
        { "insert":" and the " },
        { "insert":"italic",
          "attributes": { "italic": True }},
        { "insert":"\n\nNormal\n" },
    ]

    source = '<p>Quill</p><p>Editor</p><p><br></p><p><strong>bold</strong> and the <em>italic</em></p><p><br></p><p>Normal</p>'

    assert html.render(ops) == source

def test_empty():
    ops = [ {"insert": "\n"} ]
    source = "<p><br></p>"
    assert html.render(ops) == source

def test_link():
    ops = [
        { 'insert': "example.com", "attributes": {"link": "http://example.com"} }
    ]
    source = '<p><a href="http://example.com">example.com</a></p>'
    assert html.render(ops) == source

def test_video():
    ops = [
        {"insert":{"video":"https://www.youtube.com/embed/NAb9V08zcBE"}},
        {"insert": "\n"}
    ]
    source = '<iframe class="ql-video" frameborder="0" allowfullscreen="true" src="https://www.youtube.com/embed/NAb9V08zcBE"></iframe><p><br></p>'
    assert html.render(ops) == source

def test_colors():
    ops = [
        {"insert": "quill", "attributes": {"background": "#000000"}}
    ]

    source = '<p><span style="background-color: #000">quill</span></p>'
    assert html.render(ops) == source

    ops = [
        {"insert": "quill", "attributes": {"background": "#000000", "color": "#FFFFFF"}}
    ]

    source = '<p><span style="background-color: #000; color: #FFF">quill</span></p>'
    assert html.render(ops) == source

def test_classes():
    ops = [
        {"insert":"Quill", "attributes": {"font": "monospace", "size": "huge"}}
    ]
    source = '<p><span class="ql-font-monospace ql-size-huge">Quill</span></p>'
    assert html.render(ops) == source

    ops = [
        {"insert":"Quill", "attributes": {"font": "serif", "size": "large"}}
    ]
    source = '<p><span class="ql-font-serif ql-size-large">Quill</span></p>'
    assert html.render(ops) == source

    ops = [
        {"insert":"Quill", "attributes": {"font": "sans-serif", "size": "small"}}
    ]
    source = '<p><span class="ql-size-small">Quill</span></p>'
    assert html.render(ops) == source

def test_strong():
    ops = [
        {"insert":"Quill", "attributes": {"bold": True}}
    ]
    source = '<p><strong>Quill</strong></p>'
    assert html.render(ops) == source

    ops = [
        {"insert":"Quill", "attributes": {"strong": True}}
    ]
    source = '<p><strong>Quill</strong></p>'
    assert html.render(ops) == source

def test_em():
    ops = [
        {"insert":"Quill", "attributes": {"italic": True}}
    ]
    source = '<p><em>Quill</em></p>'
    assert html.render(ops) == source

    ops = [
        {"insert":"Quill", "attributes": {"em": True}}
    ]
    source = '<p><em>Quill</em></p>'
    assert html.render(ops) == source

def test_underline():
    ops = [
        {"insert":"Quill", "attributes": {"underline": True}}
    ]
    source = '<p><u>Quill</u></p>'
    assert html.render(ops) == source

def test_strike():
    ops = [
        {"insert":"Quill", "attributes": {"strike": True}}
    ]
    source = '<p><s>Quill</s></p>'
    assert html.render(ops) == source

def test_script():
    ops = [
        {"insert":"Quill", "attributes": {"script": "sub"}}
    ]
    source = '<p><sub>Quill</sub></p>'
    assert html.render(ops) == source
    
    ops = [
        {"insert":"Quill", "attributes": {"script": "super"}}
    ]
    source = '<p><sup>Quill</sup></p>'
    assert html.render(ops) == source

def test_header():
    ops = [
        {"insert":"Quill", "attributes": {"header": 1}}
    ]
    source = '<h1>Quill</h1>'
    assert html.render(ops) == source
    
    ops = [
        {"insert":"Quill", "attributes": {"header": 5}}
    ]
    source = '<h5>Quill</h5>'
    assert html.render(ops) == source

def test_blockquote():
    ops = [
        {"insert":"Quill", "attributes": {"blockquote": True}}
    ]
    source = '<blockquote>Quill</blockquote>'
    assert html.render(ops) == source

def test_codeblock():
    from delta.html import CODE_BLOCK_CLASS
    ops = [
        {"insert":"Quill", "attributes": {"code-block": True}}
    ]
    source = '<pre class="%s" spellcheck="false">Quill</pre>' % CODE_BLOCK_CLASS
    assert html.render(ops) == source

def test_lists():
    ops = [
        {"insert": "item 1"},
        {"insert": "\n", "attributes": {"list":"ordered"}},
        {"insert": "item 2"},
        {"insert": "\n", "attributes": {"list": "ordered"}},
        {"insert":"item 3"},
        {"insert": "\n", "attributes": {"list": "ordered"}}
    ]
    source = "<ol><li>item 1</li><li>item 2</li><li>item 3</li></ol>"
    assert html.render(ops) == source

    ops = [
        {"insert": "item 1"},
        {"insert": "\n", "attributes": {"list":"bullet"}},
        {"insert": "item 2"},
        {"insert": "\n", "attributes": {"list": "bullet"}},
        {"insert":"item 3"},
        {"insert": "\n", "attributes": {"list": "bullet"}}
    ]
    source = "<ul><li>item 1</li><li>item 2</li><li>item 3</li></ul>"
    assert html.render(ops) == source

def test_indent():
    for i in range(1, 9):
        ops = [
            {"insert": "quill", "attributes": {"indent": i}}
        ]
        source = '<p class="ql-indent-%d">quill</p>' % i
        assert html.render(ops) == source

def test_direction():
    ops = [
        {"insert": "quill"},
        {"insert": "\n", "attributes": {"direction": "rtl"}}
    ]
    source = '<p class="ql-direction-rtl">quill</p>'
    assert html.render(ops) == source

def test_align():
    ops = [
        {"insert": "quill"},
        {"insert": "\n", "attributes": {"align": "center"}}
    ]
    source = '<p class="ql-align-center">quill</p>'
    assert html.render(ops) == source

def test_image():
    ops = [
        { 'insert': {'image': 'https://i.imgur.com/ZMSUFEU.gif'} }
    ]
    source = '<p><img src="https://i.imgur.com/ZMSUFEU.gif"></p>'
    assert html.render(ops) == source
