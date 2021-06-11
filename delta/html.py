import logging
import re
from functools import wraps
from .base import Delta
from lxml.html import HtmlElement, Element
from lxml import html
from cssutils import parseStyle

# This handles the error caused by css2.1 validator on rem units
from cssutils import profile
profile._MACROS['positivelength'] = r'0|{positivenum}(em|ex|px|in|cm|mm|pt|pc|rem)'
profile._resetProperties()

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

CODE_BLOCK_CLASS = 'syntax'
VIDEO_EMBED_CLASS = 'video-embed'
PODCAST_EMBED_CLASS = 'podcast-embed'
TWITTER_EMBED_CLASS = 'twitter-embed'
INDENT_CLASS = 'indent-%d'
DIRECTION_CLASS = 'direction-%s'
ALIGN_CLASS = 'align-%s'


logger = logging.getLogger('quill')


### Helpers ###
def strip_control_bytes(text):
    try:
        return re.sub(u'[^\u0020-\uD7FF\u0009\u000A\u000D\uE000-\uFFFD\U00010000-\U0010FFFF]+', '', text)
    except:
        return text


def sub_element(root, *a, **kwargs):
    e = root.makeelement(*a, **kwargs)
    root.append(e)
    return e


def styled(element, styles):
    if element.tag != 'span':
        element = sub_element(element, 'span')
    declare = parseStyle(element.attrib.get('style', ''))
    try:
        for k, v in styles.items():
            declare.setProperty(k, v)
        element.attrib['style'] = declare.getCssText(' ')
    except:
        # Ignore invalid CSS attributes
        pass
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
    element.attrib['class'] = ' '.join(sorted(list(classes)))
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
                logger.exception('Rendering format failed: %r', e)
                el = ''
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
        return '<BlockFormat %s>' % self.name


def format(fn, name=None, cls=Format):
    if isinstance(fn, str):
        name = fn

        def wrapper(fn):
            return format(fn, name, cls)

        return wrapper
    return cls(fn, name or fn.__name__)


### Formats ###
@format
def highlight(root, op):
    return sub_element(root, 'mark')


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
def size(root, op):
    return styled(root, {'font-size': op['attributes']['size']})

@format
def font(root, op):
    return styled(root, {'font-family': op['attributes']['font']})


@format
def link(root, op):
    if type(op['attributes']['link']) is dict:
        el = sub_element(root, 'a')
        allowed_attrs = ['href', 'target']
        for key in allowed_attrs:
            value = op['attributes']['link'].get(key)
            if value or type(value) is int:
                el.attrib[key] = value
                if key == 'target' and value == '_blank':
                    el.attrib['rel'] = 'noopener'
    else:
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


def create_hyperlink(root, href):
    if href:
        a = sub_element(root, 'a')
        a.attrib['href'] = href.get('url')
        if href.get('openNewTab'):
            a.attrib['target'] = '_blank'
            a.attrib['rel'] = 'noopener noreferrer'
        return a


def set_img_attrs(img_tag, attrs):
    img_tag.attrib['alt'] = attrs.get('alt') or ''
    if attrs.get('width'):
        img_tag.attrib['width'] = str(attrs['width'])
    if attrs.get('height'):
        img_tag.attrib['height'] = str(attrs['height'])
    if attrs.get('layout'):
        img_tag.attrib['layout'] = attrs['layout']


@format
def picture(root, op):
    pic = op['insert'].get('picture')
    attributes = pic['attributes']
    raw_sources = pic['sources']

    lazy_load = attributes.get('lazy-load')
    srcset_key = 'data-srcset' if lazy_load else 'srcset'

    figure_tag = sub_element(root, 'figure')

    a = create_hyperlink(figure_tag, attributes.get('link'))

    div_tag = sub_element(a if a is not None else figure_tag, 'div')
    if attributes.get('parent_div_class'):
        div_tag.attrib['class'] = attributes['parent_div_class']

    picture_tag = sub_element(div_tag, 'picture')
    if attributes.get('picture_class'):
        picture_tag.attrib['class'] = attributes['picture_class']
    if raw_sources:
        base_src = raw_sources[-1]['srcset'][0]
        padding_bottom = base_src['height'] / base_src['width'] * 100

    for raw_source in raw_sources:
        source_tag = sub_element(picture_tag, 'source')
        source_tag.attrib[srcset_key] = ', '.join(f'{s["src"]} {s["density"]}x' for s in raw_source['srcset'])
        source_tag.attrib['type'] = raw_source['type']

        media_query = f'"(max-width: {raw_source["max-width"]}px)"' if raw_source["max-width"] else ''
        if media_query:
            source_tag.attrib['media'] = media_query

    def _create_img_tag(img_root, src_key):
        img_tag = sub_element(img_root, 'img')
        img_tag.attrib[src_key] = raw_sources[-1]['srcset'][0]['src'] if raw_sources else None
        set_img_attrs(img_tag, attributes)

    if lazy_load:
        _create_img_tag(picture_tag, 'data-src')
        noscript_tag = sub_element(picture_tag, 'noscript')
        _create_img_tag(noscript_tag, 'src')
    else:
        _create_img_tag(picture_tag, 'src')

    return figure_tag


@picture.check
def picture_check(op):
    insert = op.get('insert')
    return isinstance(insert, dict) and insert.get('picture')


def base_image(root, op, tag, key):
    img = op['insert'].get(key)
    figure = sub_element(root, 'figure')

    a = create_hyperlink(figure, img.get('link'))

    el = sub_element(a if a is not None else figure, tag)
    el.attrib['src'] = img.get('src')
    set_img_attrs(img_tag=el, attrs=img)
    return figure


@format
def image(root, op):
    return base_image(root, op, 'img', 'image')

def base_video(root, op, tag, key):
    vid = op['insert'].get(key)
    container = sub_element(root, 'div')

    href = vid.get('link')
    if href:
        a = sub_element(container, 'a')
        el = sub_element(a, tag)

        a.attrib['href'] = href.get('url')
        if href.get('openNewTab'):
            a.attrib['target'] = '_blank'
            a.attrib['rel'] = 'noopener noreferrer'

    else:
        el = sub_element(container, tag)
        source = sub_element(el, 'source')
        source.attrib['src'] = vid.get('src')
        source.attrib['type'] = vid.get('type')

    el.attrib['alt'] = vid.get('alt') or ''
    if vid.get('autoplay'):
        el.attrib['autoplay'] = str(vid['autoplay'])
    if vid.get('controls'):
        el.attrib['controls'] = str(vid['controls'])
    if vid.get('loop'):
        el.attrib['loop'] = str(vid['loop'])
    if vid.get('muted'):
        el.attrib['muted'] = str(vid['muted'])
    return container

@format
def video(root, op):
    return base_video(root, op, 'video', 'video')


@video.check
def video_check(op):
    insert = op.get('insert')
    return isinstance(insert, dict) and insert.get('video')

@image.check
def image_check(op):
    insert = op.get('insert')
    return isinstance(insert, dict) and insert.get('image')


@format
def amp_image(root, op):
    return base_image(root, op, 'amp-img', 'amp_image')


@amp_image.check
def amp_image_check(op):
    insert = op.get('insert')
    return isinstance(insert, dict) and insert.get('amp_image')


@format
def divider(root, op):
    return sub_element(root, 'hr')


@divider.check
def divider_check(op):
    insert = op.get('insert')
    return isinstance(insert, dict) and isinstance(insert.get('divider'), bool)


@format
def video_embed(root, op):
    insert = op.get('insert')
    video = insert.get('video_embed', {})
    figure = sub_element(root, 'figure')
    figure.attrib.update({
        'class': VIDEO_EMBED_CLASS
    })
    iframe = sub_element(figure, 'iframe')
    iframe.attrib.update({
        'frameborder': '0',
        'scrolling': 'no',
        'allow': 'accelerometer; encrypted-media; gyroscope; picture-in-picture',
        'allowfullscreen': None,
        'mozallowfullscreen': None,
        'webkitallowfullscreen': None,
        'oallowfullscreen': None,
        'msallowfullscreen': None,
        'allowtransparency': 'true',
        'src': video.get('src'),
    })
    if video.get('class'):
        iframe.attrib['class'] = video.get('class')
    if video.get('name'):
        iframe.attrib['name'] = video.get('name')

    if video.get('script'):
        script = sub_element(figure, 'script')
        script.attrib.update({
            'async': None,
            'src': video.get('script')
        })

    return figure


@video_embed.check
def video_embed_check(op):
    insert = op.get('insert')
    return isinstance(insert, dict) and insert.get('video_embed')


@format
def amp_video_embed(root, op):
    pass


@amp_video_embed.check
def amp_video_embed_check(op):
    insert = op.get('insert')
    return isinstance(insert, dict) and insert.get('amp_video_embed')


@format
def podcast_embed(root, op):
    insert = op.get('insert')
    podcast = insert.get('podcast_embed', {})
    figure = sub_element(root, 'figure')
    figure.attrib.update({
        'class': PODCAST_EMBED_CLASS
    })
    source = podcast.get('src', '')
    if 'transistor.fm' in source:
        iframe = sub_element(figure, 'iframe')
        iframe.attrib.update({
            'frameborder': '0',
            'style': 'width:100%;height: 200px',
            'scrolling': 'no',
            'seamless': 'true',
            'src': source,
        })
    elif 'buzzsprout.com' in source:
        accId, podId = source.split('/')[-1].split('-')
        div = sub_element(figure, 'div')
        div.attrib.update({
            'id': f'buzzsprout-player-{podId}',
        })
        script = sub_element(figure, 'script')
        script.attrib.update({
            'async': 'true',
            'src': f'https://www.buzzsprout.com/{accId}/{podId}.js?container_id=buzzsprout-player-{podId}&player=small',
            'type': 'text/javascript',
            'charset': 'utf-8'
        })
    elif 'soundcloud.com' in source:
        iframe = sub_element(figure, 'iframe')
        iframe.attrib.update({
            'frameborder': '0',
            'style': 'width:100%;',
            'scrolling': 'no',
            'allow': 'autoplay',
            'src': f'{source}&color=%23ff5500&auto_play=false&hide_related=false&show_comments=true&show_user=true&show_reposts=false&show_teaser=true&visual=true',
        })
    return figure


@podcast_embed.check
def podcast_embed_check(op):
    insert = op.get('insert')
    return isinstance(insert, dict) and insert.get('podcast_embed')


@format
def twitter_embed(root, op):
    insert = op.get('insert')
    twitter = insert.get('twitter_embed', {})
    figure = sub_element(root, 'figure')
    figure.attrib.update({
        'class': TWITTER_EMBED_CLASS
    })
    source = twitter.get('src', '')

    if 'twitter' in source:
        tweet_id, username = source.split(':')[1].split('-')
        blockquote = sub_element(figure, 'blockquote')
        blockquote.attrib.update({
            'class': 'twitter-tweet'
        })
        anchor = sub_element(blockquote, 'a')
        anchor.attrib.update({
            'href': f'https://twitter.com/{username}/status/{tweet_id}?ref_src=twsrc%5Etfw'
        })
        script = sub_element(figure, 'script')
        script.attrib.update({
            'src': 'https://platform.twitter.com/widgets.js'
        })
    return figure


@twitter_embed.check
def twitter_embed_check(op):
    insert = op.get('insert')
    return isinstance(insert, dict) and insert.get('twitter_embed')
    

### Block Formats ###
LIST_TYPES = {'ordered': 'ol', 'bullet': 'ul', 'checked': 'ul', 'unchecked': 'ul'}


@format('list', cls=BlockFormat)
def list_block(block, attrs):
    block.tag = 'li'
    previous = block.getprevious()

    while previous is not None and previous.tag == 'comment':
        previous = previous.getprevious()

    list_type = attrs['list']
    list_tag = LIST_TYPES.get(list_type, 'ol')

    if previous is not None:
        checked_continues = 'data-checked' in previous.attrib and attrs.get('list') in ['checked', 'unchecked']
        bullet_continues = 'data-checked' not in previous.attrib and attrs.get('list') == 'bullet'

    if previous is not None and previous.tag == list_tag and (
            list_tag == 'ol' or checked_continues or bullet_continues
    ):
        list_el = previous
    else:
        list_el = sub_element(block.getparent(), list_tag)
    if list_type in ['checked', 'unchecked']:
        list_el.attrib['data-checked'] = None
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


@format('code-block', cls=BlockFormat)
def code_block(root, op):
    root.tag = 'pre'
    root.attrib.update({
        'class': CODE_BLOCK_CLASS
    })
    return root


@format('id-attribute', cls=BlockFormat)
def id_attribute(root, op):
    root.attrib.update({
        'id': op['id-attribute']
    })


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
    block = None
    if attrs.get('header') == 2 and not attrs.get('id-attribute'):
        attrs['id-attribute'] = re.sub(
            '\s+', '_',re.sub('^[^a-zA-Z\s]*|[^a-zA-Z0-9\s]', '', delta.document())
        ).lower()
    for op in delta.ops:
        if isinstance(op.get('insert'), dict) and ('image' in op['insert'] or 'picture' in op['insert'] or 'divider' in op['insert']):
            append_op(root, op)
        elif isinstance(op.get('insert'), dict) and 'form_embed' in op['insert']:
            if isinstance(op['insert']['form_embed'], str):
                form = html.fragment_fromstring(op['insert']['form_embed'])
                root.append(form)
        else:
            if block is None:
                block = sub_element(root, 'p')

            append_op(block, op)

    if block is None:
        block = root

    if len(block) <= 0 and not block.text:
        br = sub_element(block, 'br')

    for fmt in BlockFormat.all:
        root = fmt(block, attrs)


def append_comment(root, delta):
    block = sub_element(root, 'comment')
    for op in delta.ops:
        text = op.get('insert')
        if block.text:
            block.text += text
        else:
            block.text = text


def render(delta, method='html', pretty=False, restrict_header=None):
    if not isinstance(delta, Delta):
        delta = Delta(delta)

    wcount = 0
    restrict_header_inserted = False
    root = html.fragment_fromstring('<template></template>')
    for line, attrs, index in delta.iter_lines():
        append_line(root, line, attrs, index)
        wcount = sum(map(lambda op: len(((strip_control_bytes(op.get('insert')) if isinstance(op.get('insert'), str) else '') or '').split(' ')), line.ops), wcount)
        if restrict_header and wcount > 100 and not restrict_header_inserted:
            restrict_header_inserted = True
            append_comment(root, Delta([{'insert': restrict_header}]))

    if restrict_header and restrict_header_inserted:
        append_comment(root, Delta([{'insert': restrict_header}]))

    result = ''.join(
        html.tostring(
            child, method=method, with_tail=True, encoding='unicode', pretty_print=pretty
        ).replace('<comment>', '<!--').replace('</comment>', '-->')
        for child in root
    )

    # SGM - Hack to combine <pre> tags together
    # TODO - Fix this at the rendering level
    result = re.sub(r'\<\/pre\>\s*\<pre[^\>]*\>', '\n', result)
    return result
