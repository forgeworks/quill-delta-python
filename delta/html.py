import logging
from functools import wraps
from .base import Delta
from lxml.html import HtmlElement, Element
from lxml import html
from cssutils import parseStyle

CLASSES = {
    'font': {
        'serif': 'ql-font-serif',
        'monospace': 'ql-font-monospace'
    },
    'size': {
        'small': 'ql-size-small',
        'large': 'ql-size-large',
        'huge': 'ql-size-huge',
    }
}

CODE_BLOCK_CLASS = 'ql-syntax'
VIDEO_IFRAME_CLASS = 'ql-video'
INDENT_CLASS = 'ql-indent-%d'
DIRECTION_CLASS = 'ql-direction-%s'
ALIGN_CLASS = 'ql-align-%s'


logger = logging.getLogger('quill')


### Helpers ###
def sub_element(root, *a, **kwargs):
    e = root.makeelement(*a, **kwargs)
    root.append(e)
    return e

def styled(element, styles):
    if element.tag != 'span':
        element = sub_element(element, 'span')
    declare = parseStyle(element.attrib.get('style', ''))
    for k, v in styles.items():
        declare.setProperty(k, v)
    element.attrib['style'] = declare.getCssText(' ')
    return element

def classed(element, *classes):
    if element.tag != 'span':
        element = sub_element(element, 'span')
    return add_class(element, *classes)

def add_class(element, *classes):
    current = element.attrib.get('class')
    if current:
        current = set(current.split())
    else:
        current = set()
    classes = current.union(set(classes))
    element.attrib['class'] = " ".join(sorted(list(classes)))
    return element


### Registry ###
class Format:
    all = []

    def __init__(self, fn, name):
        self.all.append(self)
        self.name = name
        self.fn = fn
        self.check_fn = None

    def __call__(self, root, op):
        if self._check(op):
            try:
                el =  self.fn(root, op)
            except Exception as e:
                logger.error("Rendering format failed: %r", e)
                el = ""
            return el
        return root

    def check(self, fn):
        self.check_fn = fn
        return fn

    def _check(self, op):
        if self.check_fn:
            return self.check_fn(op)
        
        attrs = op.get('attributes', None)
        if attrs and self.name in attrs:
            return True
        return False

def format(fn, name=None, cls=Format):
    if isinstance(fn, str):
        name = fn
        def wrapper(fn):
            return format(fn, name, cls)
        return wrapper
    return cls(fn, name or fn.__name__)


class BlockFormat(Format):
    """
    Block formats change the entire line through the attrs of the endline, not through
    something like the insert.
    """
    all = []

    def __init__(self, fn, name):
        self.all.append(self)
        self.name = name
        self.fn = fn
        self.check_fn = None

    def __call__(self, root, attrs):
        if self.name in attrs:
            root = self.fn(root, attrs)
        return root

    def __repr__(self):
        return "<BlockFormat %s>" % self.name


### Formats ###
@format
def header(root, op):
    root.tag = 'h%s' % op['attributes']['header']
    return root

@format
def strong(root, op):
    return sub_element(root, 'strong')

@format
def bold(root, op):
    return strong.fn(root, op)

@format
def em(root, op):
    return sub_element(root, 'em')

@format
def italic(root, op):
    return em.fn(root, 'em')

@format
def underline(root, op):
    return sub_element(root, 'u')

@format
def strike(root, op):
    return sub_element(root, 's')

@format
def script(root, op):
    if op['attributes']['script'] == 'super':
        return sub_element(root, 'sup')
    if op['attributes']['script'] == 'sub':
        return sub_element(root, 'sub')
    return root

@format
def background(root, op):
    return styled(root, {'background-color': op['attributes']['background']})

@format
def color(root, op):
    return styled(root, {'color': op['attributes']['color']})

@format
def link(root, op):
    el = sub_element(root, 'a')
    el.attrib['href'] = op['attributes']['link']
    return el

@format
def indent(root, op):
    level = op['attributes']['indent']
    if level >= 1 and level <= 8:
        return add_class(root, INDENT_CLASS % level)
    return root

@format
def classes(root, op):
    attrs = op.get('attributes', None)
    if attrs:
        for name, options in CLASSES.items():
            value = op['attributes'].get(name)
            if value in options:
                root = classed(root, options[value])
    return root

@classes.check
def classes_check(op):
    return True

@format
def image(root, op):
    el = sub_element(root, 'img')
    el.attrib['src'] = op['insert']['image']
    return el

@image.check
def image_check(op):
    insert = op.get('insert')
    return isinstance(insert, dict) and insert.get('image')

@format
def video(root, op):
    insert = op.get('insert')
    iframe = root.makeelement('iframe')
    iframe.attrib.update({
        'class': VIDEO_IFRAME_CLASS,
        'frameborder': '0',
        'allowfullscreen': 'true',
        'src': op['insert']['video']
    })
    root.addprevious(iframe)
    return iframe

@video.check
def video_check(op):
    insert = op.get('insert')
    return isinstance(insert, dict) and insert.get('video')


### Block Formats ###
LIST_TYPES = {'ordered': 'ol', 'bullet': 'ul'}

@format('list', cls=BlockFormat)
def list_block(block, attrs):
    block.tag = 'li'
    previous = block.getprevious()
    list_tag = LIST_TYPES.get(attrs['list'], 'ol')
    if previous is not None and previous.tag == list_tag:
        list_el = previous
    else:
        list_el = sub_element(block.getparent(), list_tag)
    list_el.append(block)
    return block

@format('direction', cls=BlockFormat)
def list_block(block, attrs):
    return add_class(block, DIRECTION_CLASS % attrs['direction'])

@format('align', cls=BlockFormat)
def list_block(block, attrs):
    return add_class(block, ALIGN_CLASS % attrs['align'])

@format('header', cls=BlockFormat)
def header_block(block, attrs):
    block.tag = 'h%s' % attrs['header']
    return block

@format('blockquote', cls=BlockFormat)
def blockquote(block, attrs):
    block.tag = 'blockquote'
    return block

@format("code-block")
def code_block(root, op):
    root.tag = 'pre'
    root.attrib.update({
        'class': CODE_BLOCK_CLASS,
        'spellcheck': 'false'
    })
    return root


### Processors ###
def append_op(root, op):
    for fmt in Format.all:
        root = fmt(root, op)

    text = op.get('insert')
    if isinstance(text, str) and text:
        if list(root):
            last = root[-1]
            if last.tail:
                last.tail += text
            else:
                last.tail = text
        else:
            if root.text:
                root.text += text
            else:
                root.text = text


def append_line(root, delta, attrs, index):
    block = sub_element(root, 'p')
    
    for op in delta.ops:
        append_op(block, op)

    if len(block) <= 0 and not block.text:
        br = sub_element(block, 'br')

    for fmt in BlockFormat.all:
        root = fmt(block, attrs)


def render(delta, method='html', pretty=False):
    if not isinstance(delta, Delta):
        delta = Delta(delta)

    root = html.fragment_fromstring("<template></template>")
    for line, attrs, index in delta.iter_lines():
        append_line(root, line, attrs, index)

    result = "".join(
        html.tostring(child, method=method, with_tail=True, encoding='unicode', pretty_print=pretty) 
        for child in root)
    return result
