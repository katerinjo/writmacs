from random import random, randint
from .util import *

"""
Emphasize text.

Text: unicode italic characters
Markdown: wrap in asterisks
HTML: wrap with <em> tag
"""
emphasis: Macro = multi_macro({
            ('txt',): keymapper('italic'),
            ('md',): wrapper('*'),
            ('html',): taggifier('em')
        })

def apply_keymap(fields, context):
    """
    Apply a keymapping to text.

    Fields are:
      - keymap name
      - text to be transformed
    """
    keymap, builder = fields
    return keymapper(keymap)([builder], context)

def monospaced(fields, context):
    """
    Make text monospaced.

    In HTML: use tags
    In Markdown: use backticks
    In Text: use Unicode characters
    """
    content = fields[0]
    target = context['target']
    if target == 'md':
        return wrapper('`')([content], context)
    if target == 'html':
        multiline = False
        for chunk in content:
            if type(chunk) is str and '\n' in chunk:
                multiline = True
                break
        if multiline:
            tag = 'pre'
        else:
            tag = 'code'
        return taggifier(tag)([content], context)
    if target == 'txt':
        return keymapper('monospaced')([content], context)

def rotated(fields, context):
    """
    Rotate text upside-down.

    Unicode characters are used in all cases because there's no HTML
    support for this.
    """
    content = fields[0]
    flipped, data_out = keymapper('rotated')(fields, context)
    rev_content = list(reversed(flipped))
    return rev_content, data_out

def section(fields, context):
    """
    Demarcate a body of text and its heading.

    In Markdown and text, merely mark the heading.

    For HTML, wrap the heading in <h3> tags and the entire thing in
    <section> tags
    """
    target = context['target']
    heading, body = fields
    if target in ['md', 'txt']:
        return ['## ', *heading, '\n\n', *body], {}
    else:
        heading_builder, heading_data = taggifier('h3')([heading], context)
        body_builder, body_data = taggifier('section')([body], context)

        return heading_builder + body_builder, {**body_meta, **heading_meta}

"""
Markdown & Text: use Unicode characters to immitate proper small caps
HTML: apply a 'small-caps' class to the text
"""
small_caps = multi_macro(
    {
        ('md', 'txt'): keymapper('small-caps'),
        ('html',): taggifier('span', Class='small-caps')
    })

def snippet(fields, context):
    """
    Insert a snippet by name.
    """
    snip_name = ''.join(fields[0])
    if snip_name not in SNIPPET_CACHE:
        return [snip_name], {}
    elif context['target'] == 'md': # working with markdown, need escapes
        snippet = (SNIPPET_CACHE[snip_name]
                .replace('\\', r'\\')
                .replace('_', r'\_')
                .replace('*', r'\*'))
        return snippet, {}
    else:
        return SNIPPET_CACHE[snip_name], {}

def title(fields, __):
    """
    Assign a title to the document.

    This is metadata only; nothing is added to the body text.
    """
    return [], {'title': fields[0]}

def studly(fields, __):
    """
    Render letters as either capital or lowercase almost at random.

    The letter I is always lowercase and L is always capital, to avoid
    confusion.
    """
    def studly_str(text) -> str:
        if not type(text) is str:
            return text
        builder = []
        for character in text:
            if character in 'Ii':
                builder.append('i')
            elif character in 'Ll':
                builder.append('L')
            elif character in LETTERS:
                if random() < 0.4:
                    builder.append(character.upper())
                else:
                    builder.append(character.lower())
            else:
                builder.append(character)
        return ''.join(builder)
    return [studly_str(chunk) for chunk in fields[0]], {}

def underlined(fields, context):
    """
    Underline text.

    Markdown & Text: apply a diacritic to mimic an underline
    HTML: apply an 'underlined' class to the text
    """
    content = fields[0]
    target = context['target']
    if target == 'html':
        return taggifier('span', Class='underlined')(content, {})
    UNDERLINABLE = set(
            '0123456789ABCDEFGHIJKLMNOPRSTUVWXYZabcdefhiklmnorstuvwxz'
            + 'ĉĈĥĤŭŬêÊĴĜ().?!:-\'"+=*&^%$#@`~'
            )
    # UNDERLINE = chr(int('952', 16))
    # UNDERLINE = chr(int('331', 16))
    UNDERLINE = chr(int('320', 16))
    def underline_str(text) -> Union[str, Token]:
        if not type(text) is str:
            return text
        builder = []
        for character in text:
            if character == ' ':
                builder.append('_')
            else:
                builder.append(character)
                if character in UNDERLINABLE:
                    builder.append(UNDERLINE)
        return ''.join(builder)

    builder = []
    for chunk in content:
        builder.append(underline_str(chunk))
    return builder, {}


"""
Wrap text in sparkle emoticons.
"""
sparkly = wrapper('✧⭒͙°', '✧ﾟ☆')

def zalgo(fields, __):
    """
    Apply many random diacritics to text.
    """
    builder = []
    for chunk in fields[0]:
        if type(chunk) is str:
            for character in chunk:
                builder.append(character)
                builder.extend([chr(randint(768, 866)) for n in range(8)])
        else:
            builder.append(chunk)
    return builder, {}

keymaps = [path.stem for path in KEYMAPS_DIR.iterdir() if path.stem == '.tsv']

expanders: Dict[str, Macro] = {
        # unless overwritten, all keymaps may be invoked by name
        **{name:keymapper(name) for name in keymaps},

        'em': emphasis,

        'map': apply_keymap,
        'keymap': apply_keymap,

        'mono': monospaced,
        'monospace': monospaced,
        'monospaced': monospaced,

        'rot': rotated,
        'rotate': rotated,
        'rotated': rotated,

        'section': section,

        'smallcap': small_caps,
        'smallcaps': small_caps,
        'small-caps': small_caps,

        'snip': snippet,
        'snippet': snippet,

        'sparkly': sparkly,

        'studly': studly,

        'title': title,

        'under': underlined,
        'underline': underlined,
        'underlined': underlined,

        'void': zalgo,
        'zalgo': zalgo,
        }
organizers: Dict[str, Callable] = {}
contextualizers: Dict[str, Callable] = {}
